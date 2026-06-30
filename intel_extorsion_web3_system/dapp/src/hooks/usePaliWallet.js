import { useState, useEffect, useCallback } from 'react';

const ZKSYS_CHAIN_ID = 57057;

export const usePaliWallet = () => {
  const [account, setAccount] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [provider, setProvider] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [error, setError] = useState(null);

  const checkPali = useCallback(() => {
    const pali = window?.pali;
    if (!pali) {
      setError('Pali Wallet no detectada. Instala la extensión desde https://paliwallet.com');
      return null;
    }
    return pali;
  }, []);

  const connect = useCallback(async () => {
    setError(null);
    const pali = checkPali();
    if (!pali) return;

    try {
      // Solicitar conexión
      const accounts = await pali.request({ method: 'eth_requestAccounts' });
      const currentChainId = await pali.request({ method: 'eth_chainId' });

      setAccount(accounts[0]);
      setProvider(pali);
      setChainId(parseInt(currentChainId, 16));
      setIsConnected(true);

      // Verificar red correcta
      if (parseInt(currentChainId, 16) !== ZKSYS_CHAIN_ID) {
        setError('Por favor conecta Pali Wallet a la red zkSYS Tanenbaum Testnet (Chain ID 57057)');
      }
    } catch (err) {
      setError(err.message || 'Error al conectar con Pali Wallet');
    }
  }, [checkPali]);

  const disconnect = useCallback(() => {
    setAccount(null);
    setProvider(null);
    setChainId(null);
    setIsConnected(false);
    setError(null);
  }, []);

  const switchToZkSYS = useCallback(async () => {
    const pali = checkPali();
    if (!pali) return;
    try {
      await pali.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: '0xdf01' }], // 57057 en hex
      });
    } catch (switchError) {
      // Si la red no está agregada, agregarla
      if (switchError.code === 4902) {
        await pali.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: '0xdf01',
              chainName: 'zkSYS Tanenbaum Testnet',
              nativeCurrency: {
                name: 'Syscoin',
                symbol: 'TSYS',
                decimals: 18,
              },
              rpcUrls: ['https://rpc-zk.tanenbaum.io'],
              blockExplorerUrls: ['https://explorer-zk.tanenbaum.io'],
            },
          ],
        });
      }
    }
  }, [checkPali]);

  useEffect(() => {
    const pali = window?.pali;
    if (!pali) return;

    const handleAccountsChanged = (accounts) => {
      if (accounts.length === 0) {
        disconnect();
      } else {
        setAccount(accounts[0]);
      }
    };

    const handleChainChanged = (chainIdHex) => {
      setChainId(parseInt(chainIdHex, 16));
      window.location.reload();
    };

    pali.on('accountsChanged', handleAccountsChanged);
    pali.on('chainChanged', handleChainChanged);

    // Auto-connect si ya está autorizado
    pali.request({ method: 'eth_accounts' }).then((accounts) => {
      if (accounts && accounts.length > 0) {
        connect();
      }
    });

    return () => {
      pali.removeListener('accountsChanged', handleAccountsChanged);
      pali.removeListener('chainChanged', handleChainChanged);
    };
  }, [connect, disconnect]);

  return {
    account,
    isConnected,
    provider,
    chainId,
    error,
    connect,
    disconnect,
    switchToZkSYS,
  };
};
