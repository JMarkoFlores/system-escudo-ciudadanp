const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('IntelExtorsión Smart Contracts', function () {
  let deployer, fiscal, police, denunciante, auditor;
  let didRegistry, evidenceRegistry, caseManager, ieToken;

  beforeEach(async function () {
    [deployer, fiscal, police, denunciante, auditor] = await ethers.getSigners();

    const DIDRegistry = await ethers.getContractFactory('DIDRegistry');
    didRegistry = await DIDRegistry.deploy();

    const EvidenceRegistry = await ethers.getContractFactory('EvidenceRegistry');
    evidenceRegistry = await EvidenceRegistry.deploy();

    const CaseManager = await ethers.getContractFactory('CaseManager');
    caseManager = await CaseManager.deploy(await evidenceRegistry.getAddress());

    const IntelExtorsionToken = await ethers.getContractFactory('IntelExtorsionToken');
    ieToken = await IntelExtorsionToken.deploy();

    // Roles
    await evidenceRegistry.grantRole(await evidenceRegistry.REGISTRAR_ROLE(), await caseManager.getAddress());
    await evidenceRegistry.grantRole(await evidenceRegistry.REGISTRAR_ROLE(), deployer.address);
    await caseManager.grantRole(await caseManager.FISCAL_ROLE(), fiscal.address);
    await caseManager.grantRole(await caseManager.POLICE_ROLE(), police.address);
    await ieToken.grantRole(await ieToken.MINTER_ROLE(), deployer.address);
  });

  describe('DIDRegistry', function () {
    it('debe registrar un DID nuevo', async function () {
      const did = 'did:ethr:rollux:' + denunciante.address;
      await didRegistry.connect(deployer).registerDID(did, denunciante.address, '0xpubkey', 'https://ipfs.io/doc', '{"role":"denunciante"}');
      const doc = await didRegistry.didDocuments(did);
      expect(doc.controller).to.equal(denunciante.address);
      expect(doc.active).to.equal(true);
    });

    it('debe emitir y verificar credenciales', async function () {
      const did = 'did:ethr:rollux:' + police.address;
      await didRegistry.connect(deployer).registerDID(did, police.address, '', '', '');

      const hash = ethers.keccak256(ethers.toUtf8Bytes('cred1'));
      await didRegistry.connect(deployer).issueCredential(hash, deployer.address.toString(), did, 'OficialActivo', 0, 'uri');

      const [valid] = await didRegistry.verifyCredential(hash);
      expect(valid).to.equal(true);
    });
  });

  describe('EvidenceRegistry', function () {
    it('debe registrar evidencia y verificar integridad', async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia1'));
      const tx = await evidenceRegistry.connect(deployer).storeEvidence(
        hash,
        'QmTest123',
        'did:ethr:rollux:' + denunciante.address,
        1, // texto
        'https://metadata.json'
      );
      await tx.wait();

      const ev = await evidenceRegistry.evidencias(1);
      expect(ev.evidenceHash).to.equal(hash);

      const [valid] = await evidenceRegistry.verifyEvidence(1, hash);
      expect(valid).to.equal(true);
    });

    it('debe transferir custodia', async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia2'));
      await evidenceRegistry.connect(deployer).storeEvidence(hash, 'QmTest456', '', 2, '');

      await evidenceRegistry.connect(deployer).transferCustody(1, police.address, 'Asignacion a investigador');
      const ev = await evidenceRegistry.evidencias(1);
      expect(ev.custodian).to.equal(police.address);
    });

    it('debe rechazar hash duplicado', async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia3'));
      await evidenceRegistry.connect(deployer).storeEvidence(hash, 'QmA', '', 1, '');
      await expect(
        evidenceRegistry.connect(deployer).storeEvidence(hash, 'QmB', '', 1, '')
      ).to.be.revertedWith('EvidenceRegistry: hash ya registrado');
    });
  });

  describe('CaseManager', function () {
    it('debe crear caso y vincular evidencia', async function () {
      // Crear evidencia primero
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia_caso'));
      await evidenceRegistry.connect(deployer).storeEvidence(hash, 'QmCaso', '', 1, '');

      const tx = await caseManager.connect(police).createCase(
        'did:ethr:rollux:' + denunciante.address,
        2, // MEDIO
        'Extorsion telefonica reportada via WhatsApp',
        'https://caso.json'
      );
      await tx.wait();

      await caseManager.connect(police).vincularEvidencia(1, 1);
      const evs = await caseManager.getEvidencias(1);
      expect(evs.length).to.equal(1);
      expect(evs[0]).to.equal(1);
    });

    it('debe cambiar estado del caso', async function () {
      await caseManager.connect(police).createCase('did:test', 3, '', '');
      await caseManager.connect(police).cambiarEstado(1, 1, 'Inicio investigacion'); // EN_INVESTIGACION
      const caso = await caseManager.casos(1);
      expect(caso.estado).to.equal(1);
    });
  });

  describe('IntelExtorsionToken', function () {
    it('debe mintear token soulbound', async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia_nft'));
      await ieToken.connect(deployer).mintEvidenceToken(police.address, 1, hash, 'ipfs://QmNFT');

      expect(await ieToken.ownerOf(1)).to.equal(police.address);
      expect(await ieToken.tokenURI(1)).to.equal('ipfs://QmNFT');
    });

    it('debe prevenir transferencia soulbound', async function () {
      const hash = ethers.keccak256(ethers.toUtf8Bytes('evidencia_nft2'));
      await ieToken.connect(deployer).mintEvidenceToken(police.address, 2, hash, 'ipfs://QmNFT2');

      await expect(
        ieToken.connect(police).transferFrom(police.address, fiscal.address, 1)
      ).to.be.revertedWith('IET: token soulbound - no transferible');
    });
  });
});
