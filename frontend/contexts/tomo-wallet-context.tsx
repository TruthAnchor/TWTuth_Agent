"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"
import { ethers } from "ethers"

interface TomoWalletContextType {
  isConnected: boolean
  address: string | null
  isLoading: boolean
  error: string | null
  isCorrectChain: boolean
  connectWallet: () => Promise<void>
  disconnectWallet: () => void
  switchToStoryChain: () => Promise<void>
}

const TomoWalletContext = createContext<TomoWalletContextType | undefined>(undefined)

const STORY_CHAIN_ID = "0x13a" // 314 in hex (Filecoin mainnet)
const STORY_CHAIN_CONFIG = {
  chainId: STORY_CHAIN_ID,
  chainName: "Filecoin Mainnet",
  nativeCurrency: {
    name: "FIL",
    symbol: "FIL",
    decimals: 18,
  },
  rpcUrls: ["https://filecoin.drpc.org"],
  blockExplorerUrls: ["https://filscan.io/en/"],
}

export function TomoWalletProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [address, setAddress] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCorrectChain, setIsCorrectChain] = useState(true)

  useEffect(() => {
    checkConnection()

    if (window.ethereum) {
      window.ethereum.on("accountsChanged", handleAccountsChanged)
      window.ethereum.on("chainChanged", handleChainChanged)
    }

    return () => {
      if (window.ethereum) {
        window.ethereum.removeListener("accountsChanged", handleAccountsChanged)
        window.ethereum.removeListener("chainChanged", handleChainChanged)
      }
    }
  }, [])

  const checkConnection = async () => {
    if (window.ethereum) {
      try {
        const provider = new ethers.BrowserProvider(window.ethereum)
        const accounts = await provider.listAccounts()

        if (accounts.length > 0) {
          setIsConnected(true)
          setAddress(accounts[0].address)
          await checkChain()
        }
      } catch (err) {
        console.error("Error checking connection:", err)
      }
    }
  }

  const checkChain = async () => {
    if (window.ethereum) {
      try {
        const chainId = await window.ethereum.request({ method: "eth_chainId" })
        setIsCorrectChain(chainId === STORY_CHAIN_ID)
      } catch (err) {
        console.error("Error checking chain:", err)
      }
    }
  }

  const handleAccountsChanged = (accounts: string[]) => {
    if (accounts.length > 0) {
      setIsConnected(true)
      setAddress(accounts[0])
    } else {
      setIsConnected(false)
      setAddress(null)
    }
  }

  const handleChainChanged = () => {
    checkChain()
  }

  const connectWallet = async () => {
    if (!window.ethereum) {
      setError("Please install MetaMask or another Web3 wallet")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const provider = new ethers.BrowserProvider(window.ethereum)
      await provider.send("eth_requestAccounts", [])
      const accounts = await provider.listAccounts()

      if (accounts.length > 0) {
        setIsConnected(true)
        setAddress(accounts[0].address)
        await checkChain()
      }
    } catch (err: any) {
      console.error("Error connecting wallet:", err)
      setError(err.message || "Failed to connect wallet")
    } finally {
      setIsLoading(false)
    }
  }

  const disconnectWallet = () => {
    setIsConnected(false)
    setAddress(null)
    setError(null)
  }

  const switchToStoryChain = async () => {
    if (!window.ethereum) return

    setIsLoading(true)
    setError(null)

    try {
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: STORY_CHAIN_ID }],
      })
      setIsCorrectChain(true)
    } catch (err: any) {
      // Chain not added, try to add it
      if (err.code === 4902) {
        try {
          await window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [STORY_CHAIN_CONFIG],
          })
          setIsCorrectChain(true)
        } catch (addErr: any) {
          console.error("Error adding chain:", addErr)
          setError(addErr.message || "Failed to add Story chain")
        }
      } else {
        console.error("Error switching chain:", err)
        setError(err.message || "Failed to switch to Story chain")
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <TomoWalletContext.Provider
      value={{
        isConnected,
        address,
        isLoading,
        error,
        isCorrectChain,
        connectWallet,
        disconnectWallet,
        switchToStoryChain,
      }}
    >
      {children}
    </TomoWalletContext.Provider>
  )
}

export function useTomoWallet() {
  const context = useContext(TomoWalletContext)
  if (context === undefined) {
    throw new Error("useTomoWallet must be used within a TomoWalletProvider")
  }
  return context
}
