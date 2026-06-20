// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title DIDRegistry
 * @dev Registro de Identidades Descentralizadas (DID) para denunciantes,
 *      oficiales y entidades del sistema IntelExtorsión.
 *      Compatible con did:ethr y did:pkh.
 */
contract DIDRegistry is AccessControl {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");

    struct DIDDocument {
        string did;                  // ej: did:ethr:rollux:0x123...
        address controller;          // Dirección que controla el DID
        string publicKeyHex;         // Clave pública asociada (opcional)
        string documentURI;          // URI al documento DID completo (IPFS/HTTPS)
        bool active;
        uint256 createdAt;
        uint256 updatedAt;
        uint256 reputationScore;     // Score de reputación (0-10000)
        string metadata;             // JSON string con claims verificables
    }

    struct Credential {
        bytes32 credentialHash;      // Hash de la credencial verificable
        string issuerDID;
        string subjectDID;
        string credentialType;       // ej: "DenuncianteVerificado", "OficialActivo"
        uint256 issuedAt;
        uint256 expiresAt;
        bool revoked;
        string metadataURI;
    }

    // did string => documento
    mapping(string => DIDDocument) public didDocuments;
    // credentialHash => credencial
    mapping(bytes32 => Credential) public credentials;
    // subjectDID => lista de hashes de credenciales
    mapping(string => bytes32[]) public credentialsBySubject;
    // address => DID (mapeo inverso para lookups rápidos)
    mapping(address => string) public addressToDID;

    string[] public allDIDs;

    event DIDRegistered(string indexed did, address indexed controller, uint256 timestamp);
    event DIDUpdated(string indexed did, uint256 timestamp);
    event DIDDeactivated(string indexed did, uint256 timestamp);
    event CredentialIssued(bytes32 indexed credentialHash, string indexed issuerDID, string indexed subjectDID, uint256 timestamp);
    event CredentialRevoked(bytes32 indexed credentialHash, address indexed by, uint256 timestamp);
    event ReputationUpdated(string indexed did, uint256 newScore, uint256 timestamp);

    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ISSUER_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
    }

    function registerDID(
        string calldata _did,
        address _controller,
        string calldata _publicKeyHex,
        string calldata _documentURI,
        string calldata _metadata
    ) external onlyRole(ISSUER_ROLE) {
        require(bytes(_did).length > 0, "DIDRegistry: DID vacio");
        require(_controller != address(0), "DIDRegistry: controller invalido");
        require(bytes(didDocuments[_did].did).length == 0, "DIDRegistry: DID ya existe");

        didDocuments[_did] = DIDDocument({
            did: _did,
            controller: _controller,
            publicKeyHex: _publicKeyHex,
            documentURI: _documentURI,
            active: true,
            createdAt: block.timestamp,
            updatedAt: block.timestamp,
            reputationScore: 5000, // Score inicial neutral
            metadata: _metadata
        });

        addressToDID[_controller] = _did;
        allDIDs.push(_did);

        emit DIDRegistered(_did, _controller, block.timestamp);
    }

    function updateDIDDocument(
        string calldata _did,
        string calldata _newDocumentURI,
        string calldata _newMetadata
    ) external {
        DIDDocument storage doc = didDocuments[_did];
        require(bytes(doc.did).length > 0, "DIDRegistry: DID no existe");
        require(
            doc.controller == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "DIDRegistry: no es controller"
        );

        doc.documentURI = _newDocumentURI;
        doc.metadata = _newMetadata;
        doc.updatedAt = block.timestamp;

        emit DIDUpdated(_did, block.timestamp);
    }

    function deactivateDID(string calldata _did) external {
        DIDDocument storage doc = didDocuments[_did];
        require(bytes(doc.did).length > 0, "DIDRegistry: DID no existe");
        require(
            doc.controller == msg.sender || hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "DIDRegistry: no es controller"
        );
        doc.active = false;
        emit DIDDeactivated(_did, block.timestamp);
    }

    function issueCredential(
        bytes32 _credentialHash,
        string calldata _issuerDID,
        string calldata _subjectDID,
        string calldata _credentialType,
        uint256 _expiresAt,
        string calldata _metadataURI
    ) external onlyRole(ISSUER_ROLE) {
        require(_credentialHash != bytes32(0), "DIDRegistry: hash vacio");
        require(bytes(didDocuments[_issuerDID].did).length > 0, "DIDRegistry: issuer DID no existe");
        require(bytes(didDocuments[_subjectDID].did).length > 0, "DIDRegistry: subject DID no existe");

        credentials[_credentialHash] = Credential({
            credentialHash: _credentialHash,
            issuerDID: _issuerDID,
            subjectDID: _subjectDID,
            credentialType: _credentialType,
            issuedAt: block.timestamp,
            expiresAt: _expiresAt,
            revoked: false,
            metadataURI: _metadataURI
        });

        credentialsBySubject[_subjectDID].push(_credentialHash);

        emit CredentialIssued(_credentialHash, _issuerDID, _subjectDID, block.timestamp);
    }

    function revokeCredential(bytes32 _credentialHash) external onlyRole(ISSUER_ROLE) {
        require(credentials[_credentialHash].credentialHash != bytes32(0), "DIDRegistry: credencial no existe");
        credentials[_credentialHash].revoked = true;
        emit CredentialRevoked(_credentialHash, msg.sender, block.timestamp);
    }

    function updateReputation(string calldata _did, uint256 _newScore) external onlyRole(VERIFIER_ROLE) {
        require(_newScore <= 10000, "DIDRegistry: score maximo 10000");
        DIDDocument storage doc = didDocuments[_did];
        require(bytes(doc.did).length > 0, "DIDRegistry: DID no existe");
        doc.reputationScore = _newScore;
        emit ReputationUpdated(_did, _newScore, block.timestamp);
    }

    function verifyCredential(bytes32 _credentialHash) external view returns (bool valid, string memory status) {
        Credential storage cred = credentials[_credentialHash];
        if (cred.credentialHash == bytes32(0)) return (false, "No existe");
        if (cred.revoked) return (false, "Revocada");
        if (cred.expiresAt > 0 && block.timestamp > cred.expiresAt) return (false, "Expirada");
        return (true, "Valida");
    }

    function getCredentialsBySubject(string calldata _subjectDID) external view returns (bytes32[] memory) {
        return credentialsBySubject[_subjectDID];
    }

    function getDIDByAddress(address _addr) external view returns (string memory) {
        return addressToDID[_addr];
    }

    function didExists(string calldata _did) external view returns (bool) {
        return bytes(didDocuments[_did].did).length > 0 && didDocuments[_did].active;
    }
}
