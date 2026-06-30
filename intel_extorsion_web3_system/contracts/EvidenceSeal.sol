// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title EvidenceSeal
 * @dev Sellado secundario de evidencias digitales.
 *      Registra un hash de sellado independiente del registro principal,
 *      proporcionando doble capa de integridad criptográfica.
 *      Desplegado en zkSYS Tanenbaum Testnet (Chain ID 57057).
 */
contract EvidenceSeal is AccessControl, ReentrancyGuard {
    bytes32 public constant SEALER_ROLE = keccak256("SEALER_ROLE");

    uint256 private _sealIds;

    struct Seal {
        uint256 id;
        uint256 evidenceId;          // ID de la evidencia en EvidenceRegistry
        bytes32 sealHash;            // Hash del sellado (puede ser hash combinado)
        bytes32 originalEvidenceHash;// Hash SHA-256 de la evidencia original
        address sealedBy;            // Dirección que realizó el sellado
        uint256 timestamp;           // Block timestamp del sellado
        string metadataURI;          // URI a metadatos del sellado (acta PDF, etc.)
        bool active;                 // Si el sellado está activo
    }

    // Mapeos
    mapping(uint256 => Seal) public seals;
    mapping(bytes32 => uint256) public sealHashToSealId;       // Prevenir duplicados
    mapping(uint256 => uint256) public evidenceIdToSealId;     // Una evidencia = un seal principal
    mapping(address => uint256[]) public sealsBySealer;

    // Eventos
    event EvidenceSealed(
        uint256 indexed sealId,
        uint256 indexed evidenceId,
        bytes32 indexed sealHash,
        address sealedBy,
        uint256 timestamp
    );
    event SealRevoked(uint256 indexed sealId, address indexed by, uint256 timestamp, string motivo);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(SEALER_ROLE, msg.sender);
    }

    /**
     * @dev Registra un sellado secundario de evidencia.
     * @param _evidenceId ID de la evidencia en EvidenceRegistry.
     * @param _sealHash Hash combinado o del acta firmada.
     * @param _originalEvidenceHash Hash SHA-256 de la evidencia original.
     * @param _metadataURI URI al acta PDF firmada o metadata adicional.
     * @return sealId ID único asignado al sellado.
     */
    function seal(
        uint256 _evidenceId,
        bytes32 _sealHash,
        bytes32 _originalEvidenceHash,
        string calldata _metadataURI
    ) external onlyRole(SEALER_ROLE) nonReentrant returns (uint256 sealId) {
        require(_sealHash != bytes32(0), "EvidenceSeal: sealHash vacio");
        require(_originalEvidenceHash != bytes32(0), "EvidenceSeal: evidenceHash vacio");
        require(sealHashToSealId[_sealHash] == 0, "EvidenceSeal: hash ya sellado");

        sealId = ++_sealIds;

        seals[sealId] = Seal({
            id: sealId,
            evidenceId: _evidenceId,
            sealHash: _sealHash,
            originalEvidenceHash: _originalEvidenceHash,
            sealedBy: msg.sender,
            timestamp: block.timestamp,
            metadataURI: _metadataURI,
            active: true
        });

        sealHashToSealId[_sealHash] = sealId;
        if (_evidenceId > 0) {
            evidenceIdToSealId[_evidenceId] = sealId;
        }
        sealsBySealer[msg.sender].push(sealId);

        emit EvidenceSealed(sealId, _evidenceId, _sealHash, msg.sender, block.timestamp);
    }

    /**
     * @dev Verifica la integridad de un sellado.
     */
    function verifySeal(
        uint256 _sealId,
        bytes32 _providedSealHash,
        bytes32 _providedEvidenceHash
    ) external view returns (bool valid, string memory mensaje) {
        Seal storage s = seals[_sealId];
        if (s.id == 0) return (false, "Sellado no existe");
        if (!s.active) return (false, "Sellado revocado");
        if (s.sealHash != _providedSealHash) return (false, "SealHash no coincide");
        if (s.originalEvidenceHash != _providedEvidenceHash) return (false, "EvidenceHash no coincide");
        return (true, "Sellado verificado - Integridad confirmada");
    }

    /**
     * @dev Obtiene datos de un sellado.
     */
    function getSeal(uint256 _sealId) external view returns (Seal memory) {
        require(seals[_sealId].id != 0, "EvidenceSeal: sellado no existe");
        return seals[_sealId];
    }

    /**
     * @dev Revoca un sellado (soft delete).
     */
    function revokeSeal(uint256 _sealId, string calldata _motivo) external onlyRole(DEFAULT_ADMIN_ROLE) {
        Seal storage s = seals[_sealId];
        require(s.id != 0, "EvidenceSeal: sellado no existe");
        s.active = false;
        emit SealRevoked(_sealId, msg.sender, block.timestamp, _motivo);
    }

    /**
     * @dev Obtiene el seal ID principal de una evidencia.
     */
    function getSealByEvidenceId(uint256 _evidenceId) external view returns (uint256) {
        return evidenceIdToSealId[_evidenceId];
    }

    /**
     * @dev Obtiene todos los sellados de un sealer.
     */
    function getSealsBySealer(address _sealer) external view returns (uint256[] memory) {
        return sealsBySealer[_sealer];
    }

    /**
     * @dev Verifica si un sellado existe.
     */
    function sealExists(uint256 _sealId) external view returns (bool) {
        return seals[_sealId].id != 0;
    }

    /**
     * @dev Contador total de sellados.
     */
    function totalSeals() external view returns (uint256) {
        return _sealIds;
    }
}
