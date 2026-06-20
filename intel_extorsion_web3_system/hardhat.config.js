require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config();

const PRIVATE_KEY = process.env.PRIVATE_KEY || '0x0000000000000000000000000000000000000000000000000000000000000000';
const SYSCOIN_RPC = process.env.SYSCOIN_RPC || 'https://rpc.rollux.com';
const SYSCOIN_TESTNET_RPC = process.env.SYSCOIN_TESTNET_RPC || 'https://rpc-testnet.rollux.com';

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: '0.8.24',
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      evmVersion: 'cancun',
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
    },
    localhost: {
      url: 'http://127.0.0.1:8545',
      chainId: 31337,
    },
    rollux_testnet: {
      url: SYSCOIN_TESTNET_RPC,
      chainId: 57000,
      accounts: [PRIVATE_KEY],
    },
    rollux: {
      url: SYSCOIN_RPC,
      chainId: 570,
      accounts: [PRIVATE_KEY],
    },
  },
  etherscan: {
    apiKey: {
      rollux: process.env.ROLLUX_EXPLORER_API_KEY || '',
    },
    customChains: [
      {
        network: 'rollux',
        chainId: 570,
        urls: {
          apiURL: 'https://explorer.rollux.com/api',
          browserURL: 'https://explorer.rollux.com',
        },
      },
    ],
  },
  paths: {
    sources: './contracts',
    tests: './test',
    cache: './cache',
    artifacts: './artifacts',
  },
};
