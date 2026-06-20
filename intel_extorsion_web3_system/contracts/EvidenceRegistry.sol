// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title EvidenceRegistry
 * @dev Registro inmutable de evidencias digitales con hash SHA-256,
 *      referencia IPFS y timestamp. Soporta cadena de custodia,
 *      transferencia de custodia y verificación de integridad.
 *      Desplegado en Syscoin Rollux L2.
 */
contract EvidenceRegistry is AccessControl, ReentrancyGuard {
    bytes32 public constant REGISTRAR_ROLE = keccak256("REGISTRAR_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");
    bytes32 public constant FORENSIC_ROLE = keccak256("FORENSIC_ROLE");

    uint256 private _evidenceIds;

    struct Evidence {
        uint256 id;
        bytes32 evidenceHash;          // SHA-256 de la evidencia original
        string ipfsCID;                // Content Identifier en IPFS
        string didDenunciante;         // DID del denunciante (puede ser anónimo)
        address custodian;             // Dirección actual del custodio
        uint8 tipoEvidencia;           // 1=texto, 2=imagen, 3=audio, 4=video, 5=documento
        string metadataURI;            // URI a metadatos adicionales (JSON)
        uint256 timestamp;             // Block timestamp del registro
        bool active;                   // Si la evidencia está activa (no revocada)
        uint256 caseId;                // ID del caso asociado (0 si no asignado)
    }

    struct CustodyTransfer {
        address from;
        address to;
        uint256 timestamp;
        string motivo;
    }

    // Mapeos
    mapping(uint256 => Evidence) public evidencias;
    mapping(bytes32 => uint256) public hashToEvidenceId; // Prevenir duplicados
    mapping(uint256 => CustodyTransfer[]) public custodyHistory; // Historial por evidencia
    mapping(address => uint256[]) public evidenciasByCustodian;

    // Eventos
    event EvidenceStored(
        uint256 indexed evidenceId,
        bytes32 indexed evidenceHash,
        address indexed custodian,
        string didDenunciante,
        uint256 timestamp,
        uint8 tipoEvidencia
    );
    event CustodyTransferred(
        uint256 indexed evidenceId,
        address indexed from,
        address indexed to,
        uint256 timestamp,
        string motivo
    );
    event EvidenceRevoked(uint256 indexed evidenceId, address indexed by, uint256 timestamp, string motivo);
    event EvidenceLinkedToCase(uint256 indexed evidenceId, uint256 indexed caseId);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(REGISTRAR_ROLE, msg.sender);
        _grantRole(AUDITOR_ROLE, msg.sender);
        _grantRole(FORENSIC_ROLE, msg.sender);
    }

    /**
     * @dev Registra una nueva evidencia en la blockchain.
     * @param _evidenceHash SHA-256 de la evidencia digital.
     * @param _ipfsCID CID de IPFS donde se almacena la evidencia.
     * @param _didDenunciante DID del denunciante (puede vacío para anónimo).
     * @param _tipoEvidencia Categoría de la evidencia.
     * @param _metadataURI URI a JSON con metadatos enriquecidos.
     * @return evidenceId ID único asignado a la evidencia.
     */
    function storeEvidence(
        bytes32 _evidenceHash,
        string calldata _ipfsCID,
        string calldata _didDenunciante,
        uint8 _tipoEvidencia,
        string calldata _metadataURI
    ) external onlyRole(REGISTRAR_ROLE) nonReentrant returns (uint256 evidenceId) {
        require(_evidenceHash != bytes32(0), "EvidenceRegistry: hash vacio");
        require(bytes(_ipfsCID).length > 0, "EvidenceRegistry: IPFS CID vacio");
        require(hashToEvidenceId[_evidenceHash] == 0, "EvidenceRegistry: hash ya registrado");
        require(_tipoEvidencia > 0 && _tipoEvidencia <= 5, "EvidenceRegistry: tipo invalido");

        evidenceId = ++_evidenceIds;

        evidencias[evidenceId] = Evidence({
            id: evidenceId,
            evidenceHash: _evidenceHash,
            ipfsCID: _ipfsCID,
            didDenunciante: _didDenunciante,
            custodian: msg.sender,
            tipoEvidencia: _tipoEvidencia,
            metadataURI: _metadataURI,
            timestamp: block.timestamp,
            active: true,
            caseId: 0
        });

        hashToEvidenceId[_evidenceHash] = evidenceId;
        evidenciasByCustodian[msg.sender].push(evidenceId);

        custodyHistory[evidenceId].push(CustodyTransfer({
            from: address(0),
            to: msg.sender,
            timestamp: block.timestamp,
            motivo: "Registro inicial"
        }));

        emit EvidenceStored(evidenceId, _evidenceHash, msg.sender, _didDenunciante, block.timestamp, _tipoEvidencia);
    }

    /**
     * @dev Transfiere la custodia de una evidencia a otra dirección.
     *      Solo el custodio actual o un administrador puede transferir.
     */
    function transferCustody(
        uint256 _evidenceId,
        address _newCustodian,
        string calldata _motivo
    ) external nonReentrant {
        require(_newCustodian != address(0), "EvidenceRegistry: custodio invalido");
        Evidence storage ev = evidencias[_evidenceId];
        require(ev.id != 0, "EvidenceRegistry: evidencia no existe");
        require(ev.active, "EvidenceRegistry: evidencia revocada");
        require(
            ev.custodian == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "EvidenceRegistry: no es custodio ni admin"
        );

        address prevCustodian = ev.custodian;
        ev.custodian = _newCustodian;

        custodyHistory[_evidenceId].push(CustodyTransfer({
            from: prevCustodian,
            to: _newCustodian,
            timestamp: block.timestamp,
            motivo: _motivo
        }));

        // Actualizar índice por custodio (simplificado: no eliminamos del anterior en esta versión por gas)
        evidenciasByCustodian[_newCustodian].push(_evidenceId);

        emit CustodyTransferred(_evidenceId, prevCustodian, _newCustodian, block.timestamp, _motivo);
    }

    /**
     * @dev Vincula una evidencia a un caso existente.
     */
    function linkToCase(uint256 _evidenceId, uint256 _caseId) external onlyRole(REGISTRAR_ROLE) {
        require(evidencias[_evidenceId].id != 0, "EvidenceRegistry: evidencia no existe");
        require(_caseId > 0, "EvidenceRegistry: caseId invalido");
        evidencias[_evidenceId].caseId = _caseId;
        emit EvidenceLinkedToCase(_evidenceId, _caseId);
    }

    /**
     * @dev Revoca una evidencia (soft delete administrativo).
     *      Solo administradores pueden revocar.
     */
    function revokeEvidence(uint256 _evidenceId, string calldata _motivo) external onlyRole(DEFAULT_ADMIN_ROLE) {
        Evidence storage ev = evidencias[_evidenceId];
        require(ev.id != 0, "EvidenceRegistry: evidencia no existe");
        ev.active = false;
        emit EvidenceRevoked(_evidenceId, msg.sender, block.timestamp, _motivo);
    }

    /**
     * @dev Verifica la integridad de una evidencia comparando su hash.
     */
    function verifyEvidence(uint256 _evidenceId, bytes32 _providedHash) external view returns (bool valid, string memory mensaje) {
        Evidence storage ev = evidencias[_evidenceId];
        if (ev.id == 0) return (false, "Evidencia no existe");
        if (!ev.active) return (false, "Evidencia revocada");
        if (ev.evidenceHash == _providedHash) {
            return (true, "Hash coincide - Integridad verificada");
        }
        return (false, "Hash NO coincide - Evidencia alterada");
    }

    /**
     * @dev Obtiene el historial completo de custodia.
     */
    function getCustodyHistory(uint256 _evidenceId) external view returns (CustodyTransfer[] memory) {
        return custodyHistory[_evidenceId];
    }

    /**
     * @dev Obtiene todas las evidencias de un custodio.
     */
    function getEvidenciasByCustodian(address _custodian) external view returns (uint256[] memory) {
        return evidenciasByCustodian[_custodian];
    }

    /**
     * @dev Verifica si una evidencia existe.
     */
    function evidenceExists(uint256 _evidenceId) external view returns (bool) {
        return evidencias[_evidenceId].id != 0;
    }

    /**
     * @dev Obtiene contador total de evidencias.
     */
    function totalEvidencias() external view returns (uint256) {
        return _evidenceIds;
    }
}
