"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"
import { ethers } from "ethers"

interface FallbackWalletContextType {
  isConnected: boolean
  address: string | null
  provider: ethers.BrowserProvider | null
  signer: ethers.JsonRpcSigner | null
  connectWallet: () => Promise<void>
  disconnectWallet: () => void
}

const FallbackWalletContext = createContext<FallbackWalletContextType | undefined>(undefined)

export function FallbackWalletProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [address, setAddress] = useState<string | null>(null)
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null)
  const [signer, setSigner] = useState<ethers.JsonRpcSigner | null>(null)

  useEffect(() => {
    checkConnection()

    if (window.ethereum) {
      window.ethereum.on("accountsChanged", handleAccountsChanged)
    }

    return () => {
      if (window.ethereum) {
        window.ethereum.removeListener("accountsChanged", handleAccountsChanged)
      }
    }
  }, [])

  const checkConnection = async () => {
    if (window.ethereum) {
      try {
        const ethersProvider = new ethers.BrowserProvider(window.ethereum)
        const accounts = await ethersProvider.listAccounts()

        if (accounts.length > 0) {
          const ethersSigner = await ethersProvider.getSigner()
          setIsConnected(true)
          setAddress(accounts[0].address)
          setProvider(ethersProvider)
          setSigner(ethersSigner)
        }
      } catch (error) {
        console.error("Error checking wallet connection:", error)
      }
    }
  }

  const handleAccountsChanged = async (accounts: string[]) => {
    if (accounts.length > 0) {
      setIsConnected(true)
      setAddress(accounts[0])

      if (window.ethereum) {
        const ethersProvider = new ethers.BrowserProvider(window.ethereum)
        const ethersSigner = await ethersProvider.getSigner()
        setProvider(ethersProvider)
        setSigner(ethersSigner)
      }
    } else {
      setIsConnected(false)
      setAddress(null)
      setSigner(null)
    }
  }

  const connectWallet = async () => {
    if (!window.ethereum) {
      alert("Please install a Web3 wallet like MetaMask")
      return
    }

    try {
      const ethersProvider = new ethers.BrowserProvider(window.ethereum)
      await ethersProvider.send("eth_requestAccounts", [])
      const accounts = await ethersProvider.listAccounts()

      if (accounts.length > 0) {
        const ethersSigner = await ethersProvider.getSigner()
        setIsConnected(true)
        setAddress(accounts[0].address)
        setProvider(ethersProvider)
        setSigner(ethersSigner)
      }
    } catch (error) {
      console.error("Error connecting wallet:", error)
    }
  }

  const disconnectWallet = () => {
    setIsConnected(false)
    setAddress(null)
    setProvider(null)
    setSigner(null)
  }

  return (
    <FallbackWalletContext.Provider
      value={{
        isConnected,
        address,
        provider,
        signer,
        connectWallet,
        disconnectWallet,
      }}
    >
      {children}
    </FallbackWalletContext.Provider>
  )
}

export function useFallbackWallet() {
  const context = useContext(FallbackWalletContext)
  if (context === undefined) {
    throw new Error("useFallbackWallet must be used within a FallbackWalletProvider")
  }
  return context
}
