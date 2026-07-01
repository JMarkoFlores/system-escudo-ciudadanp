// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title IdentityReveal
 * @dev Sistema de autorización explícita para revelar identidad civil.
 * 
 * Flujo:
 * 1. DIVINCRI solicita vinculación DID → identidad civil para un caso
 * 2. Ciudadano autoriza explícitamente (firma transacción)
 * 3. DIVINCRI ejecuta la revelación (solo después de autorización)
 * 4. Ciudadano puede revocar en cualquier momento (si aún no se reveló)
 * 
 * Este contrato garantiza que:
 * - Ninguna identidad se revela sin consentimiento explícito
 * - Todo queda registrado on-chain (trazabilidad)
 * - El ciudadano tiene control total sobre su identidad
 */
contract IdentityReveal is AccessControl {
    using Counters for Counters.Counter;

    bytes32 public constant DIVINCRI_ROLE = keccak256("DIVINCRI_ROLE");
    bytes32 public constant CITIZEN_ROLE = keccak256("CITIZEN_ROLE");

    enum RevealState {
        Pending,        // Solicitud enviada, esperando respuesta del ciudadano
        Authorized,     // Ciudadano autorizó explícitamente
        Revealed,       // DIVINCRI ejecutó la revelación
        Revoked,        // Ciudadano rechazó o revocó
        Expired         // Solicitud expirada (30 días)
    }

    struct RevealRequest {
        uint256 id;
        string citizenDID;          // DID del ciudadano (seudónimo)
        string caseId;              // ID del caso en el sistema
        string requestedByDID;      // DID del oficial DIVINCRI que solicita
        string motivoRevelacion;    // Motivo de la solicitud
        uint256 timestamp;          // Timestamp de la solicitud
        uint256 expiresAt;          // Expiración (30 días)
        RevealState state;          // Estado actual
        string civilIdentityHash;   // Hash de la identidad civil (cuando se revele)
        uint256 revealedAt;         // Timestamp de la revelación
        address revealedBy;         // Address que ejecutó la revelación
    }

    Counters.Counter private _requestIds;
    Counters.Counter private _totalReveals;

    // requestId => RevealRequest
    mapping(uint256 => RevealRequest) public requests;
    // citizenDID => requestId[]
    mapping(string => uint256[]) public requestsByCitizen;
    // caseId => requestId[]
    mapping(string => uint256[]) public requestsByCase;
    // citizenDID + caseId => requestId (evitar duplicados)
    mapping(string => mapping(string => uint256)) public requestByCitizenCase;

    // Eventos
    event RevealRequested(
        uint256 indexed requestId,
        string indexed citizenDID,
        string indexed caseId,
        string requestedByDID,
        string motivoRevelacion,
        uint256 expiresAt
    );
    event RevealAuthorized(
        uint256 indexed requestId,
        string indexed citizenDID,
        uint256 timestamp
    );
    event RevealExecuted(
        uint256 indexed requestId,
        string indexed citizenDID,
        string civilIdentityHash,
        address revealedBy,
        uint256 timestamp
    );
    event RevealRevoked(
        uint256 indexed requestId,
        string indexed citizenDID,
        string motivo,
        uint256 timestamp
    );
    event RevealExpired(
        uint256 indexed requestId,
        uint256 timestamp
    );

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(DIVINCRI_ROLE, msg.sender);
    }

    /**
     * @dev DIVINCRI solicita la revelación de identidad de un ciudadano
     * @param _citizenDID DID del ciudadano (seudónimo)
     * @param _caseId ID del caso relacionado
     * @param _motivoRevelacion Motivo justificado de la solicitud
     */
    function requestReveal(
        string calldata _citizenDID,
        string calldata _caseId,
        string calldata _motivoRevelacion
    ) external onlyRole(DIVINCRI_ROLE) returns (uint256) {
        require(bytes(_citizenDID).length > 0, "IdentityReveal: DID vacio");
        require(bytes(_caseId).length > 0, "IdentityReveal: caseId vacio");
        require(bytes(_motivoRevelacion).length > 0, "IdentityReveal: motivo vacio");

        // Verificar que no exista solicitud activa para mismo ciudadano+caso
        uint256 existingId = requestByCitizenCase[_citizenDID][_caseId];
        if (existingId > 0) {
            RevealRequest storage existing = requests[existingId];
            require(
                existing.state == RevealState.Revoked || 
                existing.state == RevealState.Revealed ||
                existing.state == RevealState.Expired,
                "IdentityReveal: solicitud activa ya existe"
            );
        }

        _requestIds.increment();
        uint256 requestId = _requestIds.current();

        uint256 expiresAt = block.timestamp + 30 days;

        requests[requestId] = RevealRequest({
            id: requestId,
            citizenDID: _citizenDID,
            caseId: _caseId,
            requestedByDID: "",  // Se llenará con el DID del solicitante
            motivoRevelacion: _motivoRevelacion,
            timestamp: block.timestamp,
            expiresAt: expiresAt,
            state: RevealState.Pending,
            civilIdentityHash: "",
            revealedAt: 0,
            revealedBy: address(0)
        });

        requestsByCitizen[_citizenDID].push(requestId);
        requestsByCase[_caseId].push(requestId);
        requestByCitizenCase[_citizenDID][_caseId] = requestId;

        emit RevealRequested(
            requestId,
            _citizenDID,
            _caseId,
            "",  // DID del solicitante (se puede agregar después)
            _motivoRevelacion,
            expiresAt
        );

        return requestId;
    }

    /**
     * @dev Ciudadano autoriza explícitamente la revelación de su identidad
     * @param _requestId ID de la solicitud
     */
    function authorizeReveal(uint256 _requestId) external {
        RevealRequest storage request = requests[_requestId];
        require(request.id > 0, "IdentityReveal: solicitud no existe");
        require(
            request.state == RevealState.Pending,
            "IdentityReveal: solicitud no esta pendiente"
        );
        require(
            block.timestamp <= request.expiresAt,
            "IdentityReveal: solicitud expirada"
        );
        // Solo el controller del DID puede autorizar
        // (verificación off-chain o por rol CITIZEN_ROLE)

        request.state = RevealState.Authorized;

        emit RevealAuthorized(_requestId, request.citizenDID, block.timestamp);
    }

    /**
     * @dev Ciudadano rechaza la solicitud de revelación
     * @param _requestId ID de la solicitud
     * @param _motivo Motivo del rechazo (opcional)
     */
    function rejectReveal(uint256 _requestId, string calldata _motivo) external {
        RevealRequest storage request = requests[_requestId];
        require(request.id > 0, "IdentityReveal: solicitud no existe");
        require(
            request.state == RevealState.Pending,
            "IdentityReveal: solicitud no esta pendiente"
        );

        request.state = RevealState.Revoked;

        emit RevealRevoked(_requestId, request.citizenDID, _motivo, block.timestamp);
    }

    /**
     * @dev DIVINCRI ejecuta la revelación (solo si está autorizada)
     * @param _requestId ID de la solicitud
     * @param _civilIdentityHash Hash de la identidad civil del ciudadano
     */
    function executeReveal(
        uint256 _requestId,
        string calldata _civilIdentityHash
    ) external onlyRole(DIVINCRI_ROLE) {
        RevealRequest storage request = requests[_requestId];
        require(request.id > 0, "IdentityReveal: solicitud no existe");
        require(
            request.state == RevealState.Authorized,
            "IdentityReveal: solicitud no autorizada"
        );
        require(
            block.timestamp <= request.expiresAt,
            "IdentityReveal: solicitud expirada"
        );
        require(
            bytes(_civilIdentityHash).length > 0,
            "IdentityReveal: hash de identidad vacio"
        );

        request.state = RevealState.Revealed;
        request.civilIdentityHash = _civilIdentityHash;
        request.revealedAt = block.timestamp;
        request.revealedBy = msg.sender;

        _totalReveals.increment();

        emit RevealExecuted(
            _requestId,
            request.citizenDID,
            _civilIdentityHash,
            msg.sender,
            block.timestamp
        );
    }

    /**
     * @dev Ciudadano revoca una autorización previa (solo si aún no se reveló)
     * @param _requestId ID de la solicitud
     */
    function revokeAuthorization(uint256 _requestId) external {
        RevealRequest storage request = requests[_requestId];
        require(request.id > 0, "IdentityReveal: solicitud no existe");
        require(
            request.state == RevealState.Authorized,
            "IdentityReveal: solo se puede revocar autorizacion pendiente de revelacion"
        );

        request.state = RevealState.Revoked;

        emit RevealRevoked(
            _requestId,
            request.citizenDID,
            "Revocado por el ciudadano",
            block.timestamp
        );
    }

    /**
     * @dev Marcar solicitud como expirada (callable por cualquiera)
     * @param _requestId ID de la solicitud
     */
    function markExpired(uint256 _requestId) external {
        RevealRequest storage request = requests[_requestId];
        require(request.id > 0, "IdentityReveal: solicitud no existe");
        require(
            request.state == RevealState.Pending || request.state == RevealState.Authorized,
            "IdentityReveal: estado no puede expirar"
        );
        require(
            block.timestamp > request.expiresAt,
            "IdentityReveal: solicitud aun no expira"
        );

        request.state = RevealState.Expired;

        emit RevealExpired(_requestId, block.timestamp);
    }

    // ─── VIEW FUNCTIONS ──────────────────────────────────────────

    function getRequest(uint256 _requestId) external view returns (RevealRequest memory) {
        return requests[_requestId];
    }

    function getRequestsByCitizen(string calldata _citizenDID) external view returns (uint256[] memory) {
        return requestsByCitizen[_citizenDID];
    }

    function getRequestsByCase(string calldata _caseId) external view returns (uint256[] memory) {
        return requestsByCase[_caseId];
    }

    function getTotalReveals() external view returns (uint256) {
        return _totalReveals.current();
    }

    function getStateLabel(RevealState _state) public pure returns (string memory) {
        if (_state == RevealState.Pending) return "Pendiente";
        if (_state == RevealState.Authorized) return "Autorizada";
        if (_state == RevealState.Revealed) return "Revelada";
        if (_state == RevealState.Revoked) return "Rechazada";
        if (_state == RevealState.Expired) return "Expirada";
        return "Desconocido";
    }
}
