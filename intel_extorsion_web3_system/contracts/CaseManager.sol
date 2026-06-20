// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./EvidenceRegistry.sol";

/**
 * @title CaseManager
 * @dev Gestiona casos de extorsión, vinculando múltiples evidencias,
 *      asignando oficiales y manteniendo estados de investigación.
 */
contract CaseManager is AccessControl, ReentrancyGuard {
    bytes32 public constant FISCAL_ROLE = keccak256("FISCAL_ROLE");
    bytes32 public constant POLICE_ROLE = keccak256("POLICE_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");

    uint256 private _caseIds;

    enum EstadoCaso {
        ABIERTO,
        EN_INVESTIGACION,
        EVIDENCIA_COMPLETA,
        RESUELTO,
        ARCHIVADO,
        CERRADO_FAVORABLE
    }

    enum NivelRiesgo {
        BAJO,
        MEDIO,
        ALTO,
        CRITICO
    }

    struct Caso {
        uint256 id;
        string didDenunciante;
        address creador;
        EstadoCaso estado;
        NivelRiesgo nivelRiesgo;
        string resumen;
        uint256[] evidenceIds;
        address[] oficialesAsignados;
        uint256 createdAt;
        uint256 updatedAt;
        bool active;
        string metadataURI;
    }

    struct EstadoChange {
        EstadoCaso estadoAnterior;
        EstadoCaso estadoNuevo;
        address changedBy;
        uint256 timestamp;
        string motivo;
    }

    mapping(uint256 => Caso) public casos;
    mapping(uint256 => EstadoChange[]) public estadoHistory;
    mapping(address => uint256[]) public casosByOficial;
    mapping(string => uint256[]) public casosByDID; // DID denunciante

    EvidenceRegistry public evidenceRegistry;

    event CasoCreado(
        uint256 indexed caseId,
        string indexed didDenunciante,
        address indexed creador,
        NivelRiesgo nivelRiesgo,
        uint256 timestamp
    );
    event EstadoCambiado(
        uint256 indexed caseId,
        EstadoCaso estadoAnterior,
        EstadoCaso estadoNuevo,
        address indexed changedBy,
        uint256 timestamp
    );
    event OficialAsignado(uint256 indexed caseId, address indexed oficial);
    event EvidenciaVinculada(uint256 indexed caseId, uint256 indexed evidenceId);
    event CasoArchivado(uint256 indexed caseId, address indexed by, string motivo);

    constructor(address _evidenceRegistryAddress) {
        require(_evidenceRegistryAddress != address(0), "CaseManager: direccion invalida");
        evidenceRegistry = EvidenceRegistry(_evidenceRegistryAddress);
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
        _grantRole(FISCAL_ROLE, msg.sender);
        _grantRole(POLICE_ROLE, msg.sender);
    }

    function createCase(
        string calldata _didDenunciante,
        NivelRiesgo _nivelRiesgo,
        string calldata _resumen,
        string calldata _metadataURI
    ) external onlyRole(POLICE_ROLE) nonReentrant returns (uint256 caseId) {
        caseId = ++_caseIds;

        casos[caseId] = Caso({
            id: caseId,
            didDenunciante: _didDenunciante,
            creador: msg.sender,
            estado: EstadoCaso.ABIERTO,
            nivelRiesgo: _nivelRiesgo,
            resumen: _resumen,
            evidenceIds: new uint256[](0),
            oficialesAsignados: new address[](0),
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            active: true,
            metadataURI: _metadataURI
        });

        casosByDID[_didDenunciante].push(caseId);
        casosByOficial[msg.sender].push(caseId);

        emit CasoCreado(caseId, _didDenunciante, msg.sender, _nivelRiesgo, block.timestamp);
    }

    function asignarOficial(uint256 _caseId, address _oficial) external onlyRole(FISCAL_ROLE) {
        require(_oficial != address(0), "CaseManager: oficial invalido");
        Caso storage c = casos[_caseId];
        require(c.id != 0, "CaseManager: caso no existe");
        require(c.active, "CaseManager: caso archivado");

        c.oficialesAsignados.push(_oficial);
        casosByOficial[_oficial].push(_caseId);
        c.updatedAt = block.timestamp;

        emit OficialAsignado(_caseId, _oficial);
    }

    function cambiarEstado(
        uint256 _caseId,
        EstadoCaso _nuevoEstado,
        string calldata _motivo
    ) external onlyRole(POLICE_ROLE) {
        Caso storage c = casos[_caseId];
        require(c.id != 0, "CaseManager: caso no existe");
        require(c.active, "CaseManager: caso archivado");

        EstadoCaso prev = c.estado;
        c.estado = _nuevoEstado;
        c.updatedAt = block.timestamp;

        estadoHistory[_caseId].push(EstadoChange({
            estadoAnterior: prev,
            estadoNuevo: _nuevoEstado,
            changedBy: msg.sender,
            timestamp: block.timestamp,
            motivo: _motivo
        }));

        emit EstadoCambiado(_caseId, prev, _nuevoEstado, msg.sender, block.timestamp);
    }

    function vincularEvidencia(uint256 _caseId, uint256 _evidenceId) external onlyRole(POLICE_ROLE) {
        Caso storage c = casos[_caseId];
        require(c.id != 0, "CaseManager: caso no existe");
        require(c.active, "CaseManager: caso archivado");
        require(
            evidenceRegistry.evidenceExists(_evidenceId),
            "CaseManager: evidencia no existe en EvidenceRegistry"
        );

        c.evidenceIds.push(_evidenceId);
        c.updatedAt = block.timestamp;

        // También actualizar en EvidenceRegistry
        evidenceRegistry.linkToCase(_evidenceId, _caseId);

        emit EvidenciaVinculada(_caseId, _evidenceId);
    }

    function archivarCaso(uint256 _caseId, string calldata _motivo) external onlyRole(FISCAL_ROLE) {
        Caso storage c = casos[_caseId];
        require(c.id != 0, "CaseManager: caso no existe");
        c.active = false;
        c.estado = EstadoCaso.ARCHIVADO;
        c.updatedAt = block.timestamp;
        emit CasoArchivado(_caseId, msg.sender, _motivo);
    }

    function getEvidencias(uint256 _caseId) external view returns (uint256[] memory) {
        return casos[_caseId].evidenceIds;
    }

    function getOficiales(uint256 _caseId) external view returns (address[] memory) {
        return casos[_caseId].oficialesAsignados;
    }

    function getEstadoHistory(uint256 _caseId) external view returns (EstadoChange[] memory) {
        return estadoHistory[_caseId];
    }

    function getCasosByOficial(address _oficial) external view returns (uint256[] memory) {
        return casosByOficial[_oficial];
    }

    function totalCasos() external view returns (uint256) {
        return _caseIds;
    }
}
