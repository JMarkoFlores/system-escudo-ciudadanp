const hre = require("hardhat");

async function main() {
  const networkName = hre.network.name;
  const provider = hre.ethers.provider;

  console.log(`\n🔍 Verificando conexión a: ${networkName}`);
  console.log("=".repeat(50));

  try {
    const network = await provider.getNetwork();
    console.log(`  ✓ Chain ID: ${network.chainId}`);
    console.log(`  ✓ Nombre:   ${network.name}`);

    const blockNumber = await provider.getBlockNumber();
    console.log(`  ✓ Bloque:   ${blockNumber}`);

    const balance = await provider.getBalance(
      process.env.PRIVATE_KEY
        ? new hre.ethers.Wallet(process.env.PRIVATE_KEY).address
        : hre.ethers.ZeroAddress
    );
    console.log(`  ✓ Balance:  ${hre.ethers.formatEther(balance)} SYS`);

    const feeData = await provider.getFeeData();
    console.log(`  ✓ Gas:      ${hre.ethers.formatUnits(feeData.gasPrice || 0n, "gwei")} gwei`);

    console.log("\n✅ Conexión exitosa a zkSYS Genesis Testnet\n");
    process.exit(0);
  } catch (error) {
    console.error(`\n❌ Error de conexión: ${error.message}\n`);
    process.exit(1);
  }
}

main();
