// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";


/**
 * @title IntelExtorsionToken
 * @dev NFT Soulbound (no transferible) que representa evidencias certificadas
 *      en la cadena de custodia. Desplegado en Syscoin Rollux L2.
 *      Cada token está vinculado a una evidencia del EvidenceRegistry.
 */
contract IntelExtorsionToken is ERC721, ERC721Enumerable, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");

    uint256 private _tokenIds;

    struct TokenMetadata {
        uint256 evidenceId;
        bytes32 evidenceHash;
        string ipfsURI;
        uint256 mintedAt;
        bool transferable;
    }

    mapping(uint256 => TokenMetadata) public tokenData;
    mapping(uint256 => uint256) public evidenceIdToTokenId;

    event EvidenceMinted(
        uint256 indexed tokenId,
        uint256 indexed evidenceId,
        bytes32 indexed evidenceHash,
        address to,
        uint256 timestamp
    );
    event EvidenceBurned(uint256 indexed tokenId, address indexed by, uint256 timestamp);

    constructor() ERC721("IntelExtorsion Evidence", "IEEV") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, msg.sender);
    }

    /**
     * @dev Mints un NFT soulbound de evidencia.
     *      Solo minters autorizados (backend del sistema).
     */
    function mintEvidenceToken(
        address _to,
        uint256 _evidenceId,
        bytes32 _evidenceHash,
        string calldata _ipfsURI
    ) external onlyRole(MINTER_ROLE) returns (uint256 tokenId) {
        require(_to != address(0), "IET: direccion invalida");
        require(evidenceIdToTokenId[_evidenceId] == 0, "IET: evidencia ya tokenizada");

        tokenId = ++_tokenIds;

        tokenData[tokenId] = TokenMetadata({
            evidenceId: _evidenceId,
            evidenceHash: _evidenceHash,
            ipfsURI: _ipfsURI,
            mintedAt: block.timestamp,
            transferable: false // Soulbound por defecto
        });

        evidenceIdToTokenId[_evidenceId] = tokenId;
        _safeMint(_to, tokenId);

        emit EvidenceMinted(tokenId, _evidenceId, _evidenceHash, _to, block.timestamp);
    }

    /**
     * @dev Quema un token de evidencia (solo en casos excepcionales).
     */
    function burnEvidenceToken(uint256 _tokenId) external onlyRole(BURNER_ROLE) {
        require(_ownerOf(_tokenId) != address(0), "IET: token no existe");
        uint256 evId = tokenData[_tokenId].evidenceId;
        delete evidenceIdToTokenId[evId];
        delete tokenData[_tokenId];
        _burn(_tokenId);
        emit EvidenceBurned(_tokenId, msg.sender, block.timestamp);
    }

    /**
     * @dev Override para prevenir transferencias si no es transferable.
     *      Implementa comportamiento Soulbound.
     */
    function _update(
        address to,
        uint256 tokenId,
        address auth
    ) internal override(ERC721, ERC721Enumerable) returns (address) {
        address from = super._update(to, tokenId, auth);
        // Permitir mint (from=0) y burn (to=0)
        if (from != address(0) && to != address(0)) {
            require(
                tokenData[tokenId].transferable,
                "IET: token soulbound - no transferible"
            );
        }
        return from;
    }

    function _increaseBalance(address account, uint128 value) internal override(ERC721, ERC721Enumerable) {
        super._increaseBalance(account, value);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(_ownerOf(tokenId) != address(0), "IET: token no existe");
        return tokenData[tokenId].ipfsURI;
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, ERC721Enumerable, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    function setTransferable(uint256 _tokenId, bool _transferable) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_ownerOf(_tokenId) != address(0), "IET: token no existe");
        tokenData[_tokenId].transferable = _transferable;
    }

    function getTokenByEvidenceId(uint256 _evidenceId) external view returns (uint256) {
        return evidenceIdToTokenId[_evidenceId];
    }

    function totalMinted() external view returns (uint256) {
        return _tokenIds;
    }
}
