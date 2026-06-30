const { ethers } = require('hardhat');
const fs = require('fs');
const path = require('path');

async function main() {
  const [deployer] = await ethers.getSigners();
  console.log('Deploying contracts with account:', deployer.address);
  console.log('Account balance:', (await deployer.provider.getBalance(deployer.address)).toString());

  // 1. Deploy DIDRegistry
  const DIDRegistry = await ethers.getContractFactory('DIDRegistry');
  const didRegistry = await DIDRegistry.deploy();
  await didRegistry.waitForDeployment();
  const didRegistryAddress = await didRegistry.getAddress();
  console.log('DIDRegistry deployed to:', didRegistryAddress);

  // 2. Deploy EvidenceRegistry
  const EvidenceRegistry = await ethers.getContractFactory('EvidenceRegistry');
  const evidenceRegistry = await EvidenceRegistry.deploy();
  await evidenceRegistry.waitForDeployment();
  const evidenceRegistryAddress = await evidenceRegistry.getAddress();
  console.log('EvidenceRegistry deployed to:', evidenceRegistryAddress);

  // 3. Deploy CaseManager (needs EvidenceRegistry address)
  const CaseManager = await ethers.getContractFactory('CaseManager');
  const caseManager = await CaseManager.deploy(evidenceRegistryAddress);
  await caseManager.waitForDeployment();
  const caseManagerAddress = await caseManager.getAddress();
  console.log('CaseManager deployed to:', caseManagerAddress);

  // 4. Deploy IntelExtorsionToken (Soulbound NFT)
  const IntelExtorsionToken = await ethers.getContractFactory('IntelExtorsionToken');
  const ieToken = await IntelExtorsionToken.deploy();
  await ieToken.waitForDeployment();
  const ieTokenAddress = await ieToken.getAddress();
  console.log('IntelExtorsionToken deployed to:', ieTokenAddress);

  // 5. Deploy EvidenceSeal (secondary seal contract)
  const EvidenceSeal = await ethers.getContractFactory('EvidenceSeal');
  const evidenceSeal = await EvidenceSeal.deploy();
  await evidenceSeal.waitForDeployment();
  const evidenceSealAddress = await evidenceSeal.getAddress();
  console.log('EvidenceSeal deployed to:', evidenceSealAddress);

  // 6. Grant roles to deployer and cross-contract
  console.log('Configuring roles...');

  // EvidenceRegistry roles
  await evidenceRegistry.grantRole(
    await evidenceRegistry.REGISTRAR_ROLE(),
    caseManagerAddress
  );
  await evidenceRegistry.grantRole(
    await evidenceRegistry.REGISTRAR_ROLE(),
    deployer.address
  );

  // EvidenceSeal roles
  await evidenceSeal.grantRole(await evidenceSeal.SEALER_ROLE(), deployer.address);

  // CaseManager roles
  await caseManager.grantRole(await caseManager.FISCAL_ROLE(), deployer.address);
  await caseManager.grantRole(await caseManager.POLICE_ROLE(), deployer.address);

  // Token roles
  await ieToken.grantRole(await ieToken.MINTER_ROLE(), deployer.address);

  // 7. Save deployment info
  const deploymentInfo = {
    network: (await ethers.provider.getNetwork()).name,
    chainId: Number((await ethers.provider.getNetwork()).chainId),
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      DIDRegistry: didRegistryAddress,
      EvidenceRegistry: evidenceRegistryAddress,
      CaseManager: caseManagerAddress,
      IntelExtorsionToken: ieTokenAddress,
      EvidenceSeal: evidenceSealAddress,
    },
  };

  const deploymentsDir = path.join(__dirname, '..', 'deployments');
  if (!fs.existsSync(deploymentsDir)) fs.mkdirSync(deploymentsDir);

  fs.writeFileSync(
    path.join(deploymentsDir, 'deployment.json'),
    JSON.stringify(deploymentInfo, null, 2)
  );

  fs.writeFileSync(
    path.join(deploymentsDir, 'addresses.json'),
    JSON.stringify(deploymentInfo.contracts, null, 2)
  );

  console.log('\nDeployment complete! Info saved to deployments/deployment.json');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
