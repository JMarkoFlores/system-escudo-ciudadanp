const { ethers } = require('hardhat');

async function main() {
  const gasPrice = (await ethers.provider.getFeeData()).gasPrice;
  console.log(`Gas price: ${ethers.formatUnits(gasPrice, "gwei")} gwei`);

  let totalGas = 0n;

  // DIDRegistry
  const DIDRegistry = await ethers.getContractFactory('DIDRegistry');
  const didTx = await DIDRegistry.getDeployTransaction();
  const didGas = await ethers.provider.estimateGas(didTx);
  totalGas += didGas;
  console.log(`DIDRegistry Gas: ${didGas}`);

  // EvidenceRegistry
  const EvidenceRegistry = await ethers.getContractFactory('EvidenceRegistry');
  const erTx = await EvidenceRegistry.getDeployTransaction();
  const erGas = await ethers.provider.estimateGas(erTx);
  totalGas += erGas;
  console.log(`EvidenceRegistry Gas: ${erGas}`);

  // CaseManager (needs dummy address)
  const CaseManager = await ethers.getContractFactory('CaseManager');
  const cmTx = await CaseManager.getDeployTransaction(ethers.ZeroAddress);
  const cmGas = await ethers.provider.estimateGas(cmTx);
  totalGas += cmGas;
  console.log(`CaseManager Gas: ${cmGas}`);

  // IntelExtorsionToken
  const IntelToken = await ethers.getContractFactory('IntelExtorsionToken');
  const itTx = await IntelToken.getDeployTransaction();
  const itGas = await ethers.provider.estimateGas(itTx);
  totalGas += itGas;
  console.log(`IntelToken Gas: ${itGas}`);
  
  // Roles buffer (approximate)
  const rolesBuffer = 400000n;
  totalGas += rolesBuffer;
  console.log(`Role assignments Gas buffer: ${rolesBuffer}`);

  console.log(`Total Estimated Gas Limit: ${totalGas}`);
  
  const totalCost = totalGas * gasPrice;
  console.log(`\nEstimated Cost: ${ethers.formatEther(totalCost)} SYS`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
