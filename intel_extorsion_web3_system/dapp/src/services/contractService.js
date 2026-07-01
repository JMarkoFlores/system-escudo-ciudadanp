import { ethers } from 'ethers';

const EvidenceRegistryABI = [
  "function storeEvidence(bytes32 _evidenceHash, string _ipfsCID, string _didDenunciante, uint8 _tipoEvidencia, string _metadataURI) returns (uint256)",
  "function verifyEvidence(uint256 _evidenceId, bytes32 _providedHash) view returns (bool, string)",
  "function transferCustody(uint256 _evidenceId, address _newCustodian, string _motivo)",
  "function getCustodyHistory(uint256 _evidenceId) view returns (tuple(address from, address to, uint256 timestamp, string motivo)[])",
  "function evidencias(uint256) view returns (uint256 id, bytes32 evidenceHash, string ipfsCID, string didDenunciante, address custodian, uint8 tipoEvidencia, string metadataURI, uint256 timestamp, bool active, uint256 caseId)",
  "event EvidenceStored(uint256 indexed evidenceId, bytes32 indexed evidenceHash, address indexed custodian, string didDenunciante, uint256 timestamp, uint8 tipoEvidencia)"
];

const CaseManagerABI = [
  "function createCase(string _didDenunciante, uint8 _nivelRiesgo, string _resumen, string _metadataURI) returns (uint256)",
  "function vincularEvidencia(uint256 _caseId, uint256 _evidenceId)",
  "function casos(uint256) view returns (uint256 id, string didDenunciante, address creador, uint8 estado, uint8 nivelRiesgo, string resumen, uint256 createdAt, uint256 updatedAt, bool active, string metadataURI)"
];

const DIDRegistryABI = [
  "function registerDID(string _did, address _controller, string _publicKeyHex, string _documentURI, string _metadata) returns (bool)",
  "function didDocuments(string) view returns (string did, address controller, string publicKeyHex, string documentURI, bool active, uint256 createdAt, uint256 updatedAt, uint256 reputationScore, string metadata)",
  "function verifyCredential(bytes32 _credentialHash) view returns (bool, string)"
];

const EvidenceSealABI = [
  "function seal(uint256 _evidenceId, bytes32 _sealHash, bytes32 _originalEvidenceHash, string _metadataURI) returns (uint256)",
  "function getSeal(uint256 _sealId) view returns (uint256 id, uint256 evidenceId, bytes32 sealHash, bytes32 originalEvidenceHash, address sealedBy, uint256 timestamp, string metadataURI, bool active)",
  "function verifySeal(uint256 _sealId, bytes32 _providedSealHash, bytes32 _providedEvidenceHash) view returns (bool, string)",
  "function getSealByEvidenceId(uint256 _evidenceId) view returns (uint256)",
  "function sealExists(uint256 _sealId) view returns (bool)",
  "event EvidenceSealed(uint256 indexed sealId, uint256 indexed evidenceId, bytes32 indexed sealHash, address sealedBy, uint256 timestamp)"
];

const IdentityRevealABI = [
  "function requestReveal(string _citizenDID, string _caseId, string _motivoRevelacion) returns (uint256)",
  "function authorizeReveal(uint256 _requestId)",
  "function rejectReveal(uint256 _requestId, string _motivo)",
  "function executeReveal(uint256 _requestId, string _civilIdentityHash)",
  "function revokeAuthorization(uint256 _requestId)",
  "function markExpired(uint256 _requestId)",
  "function getRequest(uint256 _requestId) view returns (tuple(uint256 id, string citizenDID, string caseId, string requestedByDID, string motivoRevelacion, uint256 timestamp, uint256 expiresAt, uint8 state, string civilIdentityHash, uint256 revealedAt, address revealedBy))",
  "function getRequestsByCitizen(string _citizenDID) view returns (uint256[])",
  "function getRequestsByCase(string _caseId) view returns (uint256[])",
  "function getTotalReveals() view returns (uint256)",
  "function getStateLabel(uint8 _state) view returns (string)",
  "event RevealRequested(uint256 indexed requestId, string indexed citizenDID, string indexed caseId, string requestedByDID, string motivoRevelacion, uint256 expiresAt)",
  "event RevealAuthorized(uint256 indexed requestId, string indexed citizenDID, uint256 timestamp)",
  "event RevealExecuted(uint256 indexed requestId, string indexed citizenDID, string civilIdentityHash, address revealedBy, uint256 timestamp)",
  "event RevealRevoked(uint256 indexed requestId, string indexed citizenDID, string motivo, uint256 timestamp)",
  "event RevealExpired(uint256 indexed requestId, uint256 timestamp)"
];

const CONTRACTS = {
  evidenceRegistry: import.meta.env.VITE_CONTRACT_EVIDENCE_REGISTRY || '',
  caseManager: import.meta.env.VITE_CONTRACT_CASE_MANAGER || '',
  didRegistry: import.meta.env.VITE_CONTRACT_DID_REGISTRY || '',
  evidenceSeal: import.meta.env.VITE_CONTRACT_EVIDENCE_SEAL || '',
  identityReveal: import.meta.env.VITE_CONTRACT_IDENTITY_REVEAL || '',
  token: import.meta.env.VITE_CONTRACT_TOKEN || '',
};

const EXPLORER_URL = import.meta.env.VITE_EXPLORER_URL || 'https://explorer-zk.tanenbaum.io';
const RPC_URL = import.meta.env.VITE_RPC_URL || 'https://rpc-zk.tanenbaum.io';

export class ContractService {
  constructor(providerOrSigner) {
    if (typeof providerOrSigner === 'string' || providerOrSigner?.request === undefined) {
      this.provider = new ethers.BrowserProvider(window.pali);
    } else {
      this.provider = new ethers.BrowserProvider(providerOrSigner);
    }
    this.signer = null;
  }

  async init() {
    this.signer = await this.provider.getSigner();
  }

  _getContract(address, abi) {
    if (!address || address === '0x0000000000000000000000000000000000000000') return null;
    return new ethers.Contract(address, abi, this.signer);
  }

  getEvidenceRegistry() {
    return this._getContract(CONTRACTS.evidenceRegistry, EvidenceRegistryABI);
  }

  getCaseManager() {
    return this._getContract(CONTRACTS.caseManager, CaseManagerABI);
  }

  getDIDRegistry() {
    return this._getContract(CONTRACTS.didRegistry, DIDRegistryABI);
  }

  getEvidenceSeal() {
    return this._getContract(CONTRACTS.evidenceSeal, EvidenceSealABI);
  }

  getIdentityReveal() {
    return this._getContract(CONTRACTS.identityReveal, IdentityRevealABI);
  }

  // ─── DID ────────────────────────────────────────────────────────

  async hasDID(did) {
    try {
      const contract = this.getDIDRegistry();
      if (!contract) return { registered: false, reason: 'no_contract' };
      const doc = await contract.didDocuments(did);
      return { registered: doc && doc[0] && doc[4] === true, doc: doc || null };
    } catch {
      return { registered: false, reason: 'error' };
    }
  }

  async registerDID(did, controller, publicKeyHex) {
    const contract = this.getDIDRegistry();
    if (!contract) throw new Error('DIDRegistry contract not configured');
    const documentURI = `https://explorer-zk.tanenbaum.io/address/${controller}`;
    const metadata = '{"created_by":"intel-extorsion-dapp","method":"challenge-signature"}';
    const tx = await contract.registerDID(did, controller, publicKeyHex, documentURI, metadata);
    await tx.wait();
    return { txHash: tx.hash };
  }

  async resolveDID(did) {
    const contract = this.getDIDRegistry();
    if (!contract) return null;
    const doc = await contract.didDocuments(did);
    if (!doc || !doc[0]) return null;
    return {
      did: doc[0],
      controller: doc[1],
      publicKey: doc[2],
      documentURI: doc[3],
      active: doc[4],
      createdAt: Number(doc[5]),
      updatedAt: Number(doc[6]),
      reputationScore: Number(doc[7]),
      metadata: doc[8],
    };
  }

  // ─── EVIDENCE REGISTRY ──────────────────────────────────────────

  async storeEvidence(evidenceHash, ipfsCID, didDenunciante, tipoEvidencia, metadataURI) {
    const contract = this.getEvidenceRegistry();
    if (!contract) throw new Error('EvidenceRegistry contract not configured');
    const tx = await contract.storeEvidence(evidenceHash, ipfsCID, didDenunciante, tipoEvidencia, metadataURI);
    const receipt = await tx.wait();
    const event = receipt.logs.find(l => {
      try {
        const parsed = contract.interface.parseLog(l);
        return parsed && parsed.name === 'EvidenceStored';
      } catch { return false; }
    });
    const evidenceId = event ? contract.interface.parseLog(event).args.evidenceId : null;
    return { txHash: tx.hash, blockNumber: receipt.blockNumber, evidenceId: Number(evidenceId) };
  }

  async verifyEvidence(evidenceId, providedHash) {
    const contract = this.getEvidenceRegistry();
    if (!contract) throw new Error('EvidenceRegistry contract not configured');
    return await contract.verifyEvidence(evidenceId, providedHash);
  }

  async getEvidence(evidenceId) {
    const contract = this.getEvidenceRegistry();
    if (!contract) throw new Error('EvidenceRegistry contract not configured');
    const ev = await contract.evidencias(evidenceId);
    return {
      id: Number(ev[0]),
      evidenceHash: ev[1],
      ipfsCID: ev[2],
      didDenunciante: ev[3],
      custodian: ev[4],
      tipoEvidencia: Number(ev[5]),
      metadataURI: ev[6],
      timestamp: Number(ev[7]),
      active: ev[8],
      caseId: Number(ev[9]),
    };
  }

  static getTipoLabel(tipo) {
    const labels = { 1: 'Texto', 2: 'Imagen', 3: 'Audio', 4: 'Video', 5: 'Documento' };
    return labels[tipo] || 'Desconocido';
  }

  // ─── EVIDENCE SEAL ──────────────────────────────────────────────

  async sealEvidence(evidenceId, sealHash, originalEvidenceHash, metadataURI) {
    const contract = this.getEvidenceSeal();
    if (!contract) throw new Error('EvidenceSeal contract not configured');
    const tx = await contract.seal(evidenceId, sealHash, originalEvidenceHash, metadataURI);
    const receipt = await tx.wait();
    const event = receipt.logs.find(l => {
      try {
        const parsed = contract.interface.parseLog(l);
        return parsed && parsed.name === 'EvidenceSealed';
      } catch { return false; }
    });
    const sealId = event ? Number(contract.interface.parseLog(event).args.sealId) : null;
    return {
      txHash: tx.hash,
      blockNumber: receipt.blockNumber,
      sealId,
      timestamp: Math.floor(Date.now() / 1000),
    };
  }

  async getSeal(sealId) {
    const contract = this.getEvidenceSeal();
    if (!contract) throw new Error('EvidenceSeal contract not configured');
    const s = await contract.getSeal(sealId);
    return {
      id: Number(s[0]),
      evidenceId: Number(s[1]),
      sealHash: s[2],
      originalEvidenceHash: s[3],
      sealedBy: s[4],
      timestamp: Number(s[5]),
      metadataURI: s[6],
      active: s[7],
    };
  }

  async verifySeal(sealId, sealHash, evidenceHash) {
    const contract = this.getEvidenceSeal();
    if (!contract) throw new Error('EvidenceSeal contract not configured');
    const result = await contract.verifySeal(sealId, sealHash, evidenceHash);
    return { valid: result[0], message: result[1] };
  }

  async getSealByEvidenceId(evidenceId) {
    const contract = this.getEvidenceSeal();
    if (!contract) return null;
    const sealId = await contract.getSealByEvidenceId(evidenceId);
    return Number(sealId) > 0 ? Number(sealId) : null;
  }

  // ─── IDENTITY REVEAL ──────────────────────────────────────────

  /**
   * Ciudadano autoriza explícitamente la revelación de su identidad
   * @param {number} requestId - ID de la solicitud
   * @returns {Promise<{txHash: string}>}
   */
  async authorizeReveal(requestId) {
    const contract = this.getIdentityReveal();
    if (!contract) throw new Error('IdentityReveal contract not configured');
    const tx = await contract.authorizeReveal(requestId);
    await tx.wait();
    return { txHash: tx.hash };
  }

  /**
   * Ciudadano rechaza la solicitud de revelación
   * @param {number} requestId - ID de la solicitud
   * @param {string} motivo - Motivo del rechazo
   * @returns {Promise<{txHash: string}>}
   */
  async rejectReveal(requestId, motivo = '') {
    const contract = this.getIdentityReveal();
    if (!contract) throw new Error('IdentityReveal contract not configured');
    const tx = await contract.rejectReveal(requestId, motivo);
    await tx.wait();
    return { txHash: tx.hash };
  }

  /**
   * Ciudadano revoca una autorización previa
   * @param {number} requestId - ID de la solicitud
   * @returns {Promise<{txHash: string}>}
   */
  async revokeAuthorization(requestId) {
    const contract = this.getIdentityReveal();
    if (!contract) throw new Error('IdentityReveal contract not configured');
    const tx = await contract.revokeAuthorization(requestId);
    await tx.wait();
    return { txHash: tx.hash };
  }

  /**
   * Obtiene el detalle de una solicitud de revelación
   * @param {number} requestId - ID de la solicitud
   * @returns {Promise<Object>}
   */
  async getRevealRequest(requestId) {
    const contract = this.getIdentityReveal();
    if (!contract) throw new Error('IdentityReveal contract not configured');
    const r = await contract.getRequest(requestId);
    const stateLabels = ['Pendiente', 'Autorizada', 'Revelada', 'Rechazada', 'Expirada'];
    return {
      id: Number(r.id),
      citizenDID: r.citizenDID,
      caseId: r.caseId,
      requestedByDID: r.requestedByDID,
      motivoRevelacion: r.motivoRevelacion,
      timestamp: Number(r.timestamp),
      expiresAt: Number(r.expiresAt),
      state: Number(r.state),
      stateLabel: stateLabels[Number(r.state)] || 'Desconocido',
      civilIdentityHash: r.civilIdentityHash,
      revealedAt: Number(r.revealedAt),
      revealedBy: r.revealedBy,
    };
  }

  /**
   * Obtiene todas las solicitudes de revelación de un ciudadano
   * @param {string} citizenDID - DID del ciudadano
   * @returns {Promise<number[]>}
   */
  async getRevealRequestsByCitizen(citizenDID) {
    const contract = this.getIdentityReveal();
    if (!contract) throw new Error('IdentityReveal contract not configured');
    const ids = await contract.getRequestsByCitizen(citizenDID);
    return ids.map(id => Number(id));
  }

  /**
   * Obtiene el total de revelaciones ejecutadas
   * @returns {Promise<number>}
   */
  async getTotalReveals() {
    const contract = this.getIdentityReveal();
    if (!contract) return 0;
    const total = await contract.getTotalReveals();
    return Number(total);
  }

  // ─── UTILITY ────────────────────────────────────────────────────

  static computeSHA256 = async (file) => {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return '0x' + hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  };

  static getForensicMetadata(file) {
    return {
      fileName: file.name,
      fileSize: file.size,
      fileSizeFormatted: file.size > 1048576
        ? `${(file.size / 1048576).toFixed(2)} MB`
        : `${(file.size / 1024).toFixed(1)} KB`,
      mimeType: file.type || 'application/octet-stream',
      lastModified: new Date(file.lastModified).toISOString(),
      captureTimestamp: new Date().toISOString(),
    };
  }

  static async getImageDimensions(file) {
    return new Promise((resolve) => {
      if (!file.type.startsWith('image/')) return resolve(null);
      const img = new Image();
      img.onload = () => resolve({ width: img.naturalWidth, height: img.naturalHeight });
      img.onerror = () => resolve(null);
      img.src = URL.createObjectURL(file);
    });
  }

  static getExplorerTxUrl(txHash) {
    return `${EXPLORER_URL}/tx/${txHash}`;
  }

  static getExplorerAddressUrl(address) {
    return `${EXPLORER_URL}/address/${address}`;
  }

  static getExplorerBlockUrl(blockNumber) {
    return `${EXPLORER_URL}/block/${blockNumber}`;
  }

  static getDIDFromAddress(address) {
    return `did:zsys:tanenbaum:${address.toLowerCase()}`;
  }
}

export default CONTRACTS;
