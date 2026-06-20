import { ethers } from 'ethers';

// ABIs mínimos para la DApp
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
  "function registerDID(string _did, address _controller, string _publicKeyHex, string _documentURI, string _metadata)",
  "function didDocuments(string) view returns (string did, address controller, string publicKeyHex, string documentURI, bool active, uint256 createdAt, uint256 updatedAt, uint256 reputationScore, string metadata)",
  "function verifyCredential(bytes32 _credentialHash) view returns (bool, string)"
];

const CONTRACTS = {
  evidenceRegistry: import.meta.env.VITE_CONTRACT_EVIDENCE_REGISTRY || '',
  caseManager: import.meta.env.VITE_CONTRACT_CASE_MANAGER || '',
  didRegistry: import.meta.env.VITE_CONTRACT_DID_REGISTRY || '',
};

const RPC_URL = import.meta.env.VITE_RPC_URL || 'https://rpc.rollux.com';

export class ContractService {
  constructor(providerOrSigner) {
    this.provider = new ethers.BrowserProvider(providerOrSigner);
    this.signer = null;
  }

  async init() {
    this.signer = await this.provider.getSigner();
  }

  getEvidenceRegistry() {
    return new ethers.Contract(CONTRACTS.evidenceRegistry, EvidenceRegistryABI, this.signer);
  }

  getCaseManager() {
    return new ethers.Contract(CONTRACTS.caseManager, CaseManagerABI, this.signer);
  }

  getDIDRegistry() {
    return new ethers.Contract(CONTRACTS.didRegistry, DIDRegistryABI, this.signer);
  }

  // Evidence Registry
  async storeEvidence(evidenceHash, ipfsCID, didDenunciante, tipoEvidencia, metadataURI) {
    const contract = this.getEvidenceRegistry();
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
    return await contract.verifyEvidence(evidenceId, providedHash);
  }

  async getEvidence(evidenceId) {
    const contract = this.getEvidenceRegistry();
    const ev = await contract.evidencias(evidenceId);
    return {
      id: Number(ev[0]),
      evidenceHash: ev[1],
      ipfsCID: ev[2],
      didDenunciante: ev[3],
      custodian: ev[4],
      tipoEvidencia: ev[5],
      metadataURI: ev[6],
      timestamp: Number(ev[7]),
      active: ev[8],
      caseId: Number(ev[9]),
    };
  }

  // Case Manager
  async createCase(didDenunciante, nivelRiesgo, resumen, metadataURI) {
    const contract = this.getCaseManager();
    const tx = await contract.createCase(didDenunciante, nivelRiesgo, resumen, metadataURI);
    const receipt = await tx.wait();
    return { txHash: tx.hash, blockNumber: receipt.blockNumber };
  }

  // DID
  async resolveDID(did) {
    const contract = this.getDIDRegistry();
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
}

export default CONTRACTS;
