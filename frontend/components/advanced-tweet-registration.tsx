"use client"

import { useState, useEffect } from "react"
import { ethers } from "ethers"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle, CheckCircle2, ArrowRight, ArrowLeft, Plus, Trash2, ExternalLink } from "lucide-react"
import { useTomoWallet } from "@/contexts/tomo-wallet-context"
import { useFallbackWallet } from "@/contexts/fallback-wallet-context"
import { useTwitterConnection } from "@/hooks/use-twitter-connection"
import { getNewIPDepositContract } from "@/lib/contracts"
import { formatTweetUrl, extractTweetId } from "@/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { StylizedButton } from "@/components/ui/stylized-button"

interface CoCreator {
  name: string
  wallet: string
}

interface CollectionConfig {
  handle: string
  mintPrice: string
  maxSupply: string
  royaltyReceiver: string
  royaltyBP: string
}

interface LicenseTermsConfig {
  defaultMintingFee: string
  currency: string
  royaltyPolicy: string
  transferable: boolean
  expiration: string
  commercialUse: boolean
  commercialAttribution: boolean
  commercialRevShare: string
  commercialRevCeiling: string
  derivativesAllowed: boolean
  derivativesAttribution: boolean
  derivativesApproval: boolean
  derivativesReciprocal: boolean
  derivativeRevCeiling: string
  uri: string
}

interface LicenseMintParams {
  licenseTermsId: string
  licensorIpId: string
  receiver: string
  amount: string
  maxMintingFee: string
  maxRevenueShare: string
}

export function AdvancedTweetRegistration() {
  const tomoWallet = useTomoWallet()
  const fallbackWallet = useFallbackWallet()
  const { isConnected: isTwitterConnected, handle } = useTwitterConnection()

  // Use Tomo wallet if connected, otherwise use fallback
  const wallet = tomoWallet.isConnected ? tomoWallet : fallbackWallet
  const isWalletConnected = wallet.isConnected
  const address = wallet.address

  const [currentStep, setCurrentStep] = useState(1)
  const [tweetUrl, setTweetUrl] = useState("")
  const [depositAmount, setDepositAmount] = useState("1")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [txHash, setTxHash] = useState<string | null>(null)

  // Collection Configuration
  const [collectionConfig, setCollectionConfig] = useState<CollectionConfig>({
    handle: handle || "",
    mintPrice: "0.01",
    maxSupply: "100",
    royaltyReceiver: address || "",
    royaltyBP: "500", // 5%
  })

  // Co-creators
  const [coCreators, setCoCreators] = useState<CoCreator[]>([])

  // License Terms (with defaults from the script)
  const [licenseTermsConfig, setLicenseTermsConfig] = useState<LicenseTermsConfig>({
    defaultMintingFee: "0",
    currency: "0x1514000000000000000000000000000000000000",
    royaltyPolicy: "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E",
    transferable: true,
    expiration: "0",
    commercialUse: true,
    commercialAttribution: true,
    commercialRevShare: "20",
    commercialRevCeiling: "0",
    derivativesAllowed: true,
    derivativesAttribution: true,
    derivativesApproval: false,
    derivativesReciprocal: true,
    derivativeRevCeiling: "0",
    uri: "",
  })

  // License Mint Parameters
  const [licenseMintParams, setLicenseMintParams] = useState<LicenseMintParams>({
    licenseTermsId: "1",
    licensorIpId: "0x0000000000000000000000000000000000000000",
    receiver: address || "",
    amount: "1",
    maxMintingFee: "0",
    maxRevenueShare: "100",
  })

  useEffect(() => {
    if (handle) {
      setCollectionConfig((prev) => ({ ...prev, handle }))
    }
  }, [handle])

  useEffect(() => {
    if (address) {
      setCollectionConfig((prev) => ({ ...prev, royaltyReceiver: address }))
      setLicenseMintParams((prev) => ({ ...prev, receiver: address }))
    }
  }, [address])

  const addCoCreator = () => {
    setCoCreators([...coCreators, { name: "", wallet: "" }])
  }

  const removeCoCreator = (index: number) => {
    setCoCreators(coCreators.filter((_, i) => i !== index))
  }

  const updateCoCreator = (index: number, field: keyof CoCreator, value: string) => {
    const updated = [...coCreators]
    updated[index][field] = value
    setCoCreators(updated)
  }

  const resetToDefaults = () => {
    setLicenseTermsConfig({
      defaultMintingFee: "0",
      currency: "0x1514000000000000000000000000000000000000",
      royaltyPolicy: "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E",
      transferable: true,
      expiration: "0",
      commercialUse: true,
      commercialAttribution: true,
      commercialRevShare: "20",
      commercialRevCeiling: "0",
      derivativesAllowed: true,
      derivativesAttribution: true,
      derivativesApproval: false,
      derivativesReciprocal: true,
      derivativeRevCeiling: "0",
      uri: "",
    })
  }

  const handleSubmit = async () => {
    if (!isWalletConnected || !isTwitterConnected) {
      setError("Please connect both your wallet and Twitter account")
      return
    }

    if (!tweetUrl) {
      setError("Please enter a tweet URL")
      return
    }

    if (!address || !handle) {
      setError("Wallet address or Twitter handle not available")
      return
    }

    setIsLoading(true)
    setError(null)
    setSuccess(null)
    setTxHash(null)

    try {
      console.log("Starting advanced tweet registration process...")

      // Extract tweet ID from URL for validation
      const tweetId = extractTweetId(tweetUrl)
      if (!tweetId) {
        throw new Error("Invalid tweet URL format")
      }

      // Format the tweet URL to ensure consistency
      const formattedTweetUrl = formatTweetUrl(tweetUrl)
      console.log("Formatted tweet URL:", formattedTweetUrl)

      // Get the appropriate provider and signer
      let signer
      if (tomoWallet.isConnected) {
        console.log("Using Tomo wallet for transaction")
        const provider = new ethers.BrowserProvider(window.ethereum)
        signer = await provider.getSigner()
      } else if (fallbackWallet.signer) {
        console.log("Using fallback wallet for transaction")
        signer = fallbackWallet.signer
      } else {
        throw new Error("No signer available")
      }

      // Get contract instance
      const ipContract = getNewIPDepositContract(signer)
      console.log("Contract instance created")

      // Prepare transaction parameters
      const recipient = address
      const validation = "twitter-verification"
      const proof = ethers.toUtf8Bytes(formattedTweetUrl)
      const collectionAddress = "0x0000000000000000000000000000000000000000" // Zero address for new collection
      const tweetHash = ethers.keccak256(ethers.toUtf8Bytes(formattedTweetUrl))

      // Convert collection config
      const collectionConfigFormatted = {
        handle: collectionConfig.handle,
        mintPrice: ethers.parseEther(collectionConfig.mintPrice),
        maxSupply: BigInt(collectionConfig.maxSupply),
        royaltyReceiver: collectionConfig.royaltyReceiver,
        royaltyBP: BigInt(collectionConfig.royaltyBP),
      }

      // Convert license terms config
      const licenseTermsConfigFormatted = {
        defaultMintingFee: BigInt(licenseTermsConfig.defaultMintingFee),
        currency: licenseTermsConfig.currency,
        royaltyPolicy: licenseTermsConfig.royaltyPolicy,
        transferable: licenseTermsConfig.transferable,
        expiration: BigInt(licenseTermsConfig.expiration),
        commercialUse: licenseTermsConfig.commercialUse,
        commercialAttribution: licenseTermsConfig.commercialAttribution,
        commercialRevShare: BigInt(licenseTermsConfig.commercialRevShare),
        commercialRevCeiling: BigInt(licenseTermsConfig.commercialRevCeiling),
        derivativesAllowed: licenseTermsConfig.derivativesAllowed,
        derivativesAttribution: licenseTermsConfig.derivativesAttribution,
        derivativesApproval: licenseTermsConfig.derivativesApproval,
        derivativesReciprocal: licenseTermsConfig.derivativesReciprocal,
        derivativeRevCeiling: BigInt(licenseTermsConfig.derivativeRevCeiling),
        uri: licenseTermsConfig.uri,
      }

      // Convert license mint params
      const licenseMintParamsFormatted = {
        licenseTermsId: BigInt(licenseMintParams.licenseTermsId),
        licensorIpId: licenseMintParams.licensorIpId,
        receiver: licenseMintParams.receiver,
        amount: BigInt(licenseMintParams.amount),
        maxMintingFee: BigInt(licenseMintParams.maxMintingFee),
        maxRevenueShare: BigInt(licenseMintParams.maxRevenueShare),
      }

      // Convert co-creators
      const coCreatorsFormatted = coCreators.map((creator) => ({
        name: creator.name,
        wallet: creator.wallet,
      }))

      console.log("Transaction parameters:", {
        recipient,
        validation,
        proof,
        collectionAddress,
        collectionConfigFormatted,
        tweetHash,
        licenseTermsConfigFormatted,
        licenseMintParamsFormatted,
        coCreatorsFormatted,
      })

      // Send transaction
      const depositAmountWei = ethers.parseEther(depositAmount)
      console.log("Sending deposit amount:", depositAmount, "IP")

      // Send transaction
      const tx = await ipContract.depositIP(
        recipient,
        validation,
        proof,
        collectionAddress,
        collectionConfigFormatted,
        tweetHash,
        licenseTermsConfigFormatted,
        licenseMintParamsFormatted,
        coCreatorsFormatted,
        {
          value: depositAmountWei,
        },
      )

      console.log("Transaction sent:", tx.hash)
      setTxHash(tx.hash)

      // Wait for transaction to be mined
      console.log("Waiting for transaction confirmation...")
      const receipt = await tx.wait()
      console.log("Transaction confirmed:", receipt)

      setSuccess("Tweet successfully registered with advanced configuration!")
    } catch (err: any) {
      console.error("Error registering tweet:", err)

      // Handle specific error types
      if (err.code === "ACTION_REJECTED") {
        setError("Transaction was rejected by the user")
      } else if (err.code === "INSUFFICIENT_FUNDS") {
        setError("Insufficient funds to complete the transaction")
      } else {
        setError(err.message || "Failed to register tweet")
      }
    } finally {
      setIsLoading(false)
    }
  }

  const isReady = isWalletConnected && isTwitterConnected

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Basic Information</h3>
            <div className="space-y-2">
              <label htmlFor="tweet-url" className="text-sm font-medium">
                Tweet URL
              </label>
              <Input
                id="tweet-url"
                placeholder="https://twitter.com/username/status/123456789"
                value={tweetUrl}
                onChange={(e) => setTweetUrl(e.target.value)}
                className="border-border/30 focus:border-primary/30 bg-background/30"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="deposit-amount" className="text-sm font-medium">
                Deposit Amount (IP)
              </label>
              <Input
                id="deposit-amount"
                type="number"
                step="0.1"
                min="0.1"
                placeholder="1"
                value={depositAmount}
                onChange={(e) => setDepositAmount(e.target.value)}
                className="border-border/30 focus:border-primary/30 bg-background/30"
              />
            </div>
          </div>
        )

      case 2:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Collection Configuration</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Handle</label>
                <Input
                  value={collectionConfig.handle}
                  onChange={(e) => setCollectionConfig({ ...collectionConfig, handle: e.target.value })}
                  className="border-border/30 focus:border-primary/30 bg-background/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Mint Price (ETH)</label>
                <Input
                  type="number"
                  step="0.001"
                  value={collectionConfig.mintPrice}
                  onChange={(e) => setCollectionConfig({ ...collectionConfig, mintPrice: e.target.value })}
                  className="border-border/30 focus:border-primary/30 bg-background/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Max Supply</label>
                <Input
                  type="number"
                  value={collectionConfig.maxSupply}
                  onChange={(e) => setCollectionConfig({ ...collectionConfig, maxSupply: e.target.value })}
                  className="border-border/30 focus:border-primary/30 bg-background/30"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Royalty BP (basis points)</label>
                <Input
                  type="number"
                  value={collectionConfig.royaltyBP}
                  onChange={(e) => setCollectionConfig({ ...collectionConfig, royaltyBP: e.target.value })}
                  className="border-border/30 focus:border-primary/30 bg-background/30"
                />
                <p className="text-xs text-muted-foreground">500 = 5%, 1000 = 10%</p>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Royalty Receiver</label>
              <Input
                value={collectionConfig.royaltyReceiver}
                onChange={(e) => setCollectionConfig({ ...collectionConfig, royaltyReceiver: e.target.value })}
                className="border-border/30 focus:border-primary/30 bg-background/30"
              />
            </div>
          </div>
        )

      case 3:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Co-Creators (Optional)</h3>
              <Button onClick={addCoCreator} size="sm" variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Add Co-Creator
              </Button>
            </div>
            {coCreators.length === 0 ? (
              <p className="text-sm text-muted-foreground">No co-creators added. You can skip this step.</p>
            ) : (
              <div className="space-y-3">
                {coCreators.map((creator, index) => (
                  <div key={index} className="flex gap-2 items-end">
                    <div className="flex-1 space-y-2">
                      <label className="text-sm font-medium">Name</label>
                      <Input
                        value={creator.name}
                        onChange={(e) => updateCoCreator(index, "name", e.target.value)}
                        placeholder="Co-creator name"
                        className="border-border/30 focus:border-primary/30 bg-background/30"
                      />
                    </div>
                    <div className="flex-1 space-y-2">
                      <label className="text-sm font-medium">Wallet Address</label>
                      <Input
                        value={creator.wallet}
                        onChange={(e) => updateCoCreator(index, "wallet", e.target.value)}
                        placeholder="0x..."
                        className="border-border/30 focus:border-primary/30 bg-background/30"
                      />
                    </div>
                    <Button onClick={() => removeCoCreator(index)} size="sm" variant="outline">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )

      case 4:
        return (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">License Terms</h3>
              <Button onClick={resetToDefaults} size="sm" variant="outline">
                Reset to Defaults
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Commercial Use</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={licenseTermsConfig.commercialUse}
                    onChange={(e) => setLicenseTermsConfig({ ...licenseTermsConfig, commercialUse: e.target.checked })}
                  />
                  <span className="text-sm">Allow commercial use</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Commercial Revenue Share (%)</label>
                <Input
                  type="number"
                  value={licenseTermsConfig.commercialRevShare}
                  onChange={(e) => setLicenseTermsConfig({ ...licenseTermsConfig, commercialRevShare: e.target.value })}
                  className="border-border/30 focus:border-primary/30 bg-background/30"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Derivatives Allowed</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={licenseTermsConfig.derivativesAllowed}
                    onChange={(e) =>
                      setLicenseTermsConfig({ ...licenseTermsConfig, derivativesAllowed: e.target.checked })
                    }
                  />
                  <span className="text-sm">Allow derivatives</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Transferable</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={licenseTermsConfig.transferable}
                    onChange={(e) => setLicenseTermsConfig({ ...licenseTermsConfig, transferable: e.target.checked })}
                  />
                  <span className="text-sm">License is transferable</span>
                </div>
              </div>
            </div>

            <div className="bg-background/30 border border-border/30 rounded-md p-4">
              <h4 className="text-sm font-medium mb-2">Advanced Settings</h4>
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="text-muted-foreground">Currency:</label>
                  <p className="font-mono">{licenseTermsConfig.currency}</p>
                </div>
                <div>
                  <label className="text-muted-foreground">Royalty Policy:</label>
                  <p className="font-mono">{licenseTermsConfig.royaltyPolicy}</p>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return null
    }
  }

  return (
    <Card className="border-accent/20">
      <CardHeader>
        <CardTitle>Advanced Tweet Registration</CardTitle>
        <CardDescription>Configure collection settings, co-creators, and license terms</CardDescription>
        <div className="flex items-center space-x-2 mt-4">
          {[1, 2, 3, 4].map((step) => (
            <div
              key={step}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium ${
                step === currentStep
                  ? "bg-primary text-primary-foreground"
                  : step < currentStep
                    ? "bg-accent text-accent-foreground"
                    : "bg-muted text-muted-foreground"
              }`}
            >
              {step}
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {!isReady && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Connection Required</AlertTitle>
            <AlertDescription>Please connect both your wallet and Twitter account to register tweets.</AlertDescription>
          </Alert>
        )}

        {isReady && renderStep()}

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert variant="default" className="bg-accent/10 border-accent/30">
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {txHash && (
          <div className="bg-background/30 border border-border/30 rounded-md p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium">Transaction Hash</h3>
              <a
                href={`https://filscan.io/en/message/${txHash}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-xs text-primary hover:text-primary/80"
              >
                View on Explorer <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </div>
            <p className="text-xs font-mono break-all">{txHash}</p>
          </div>
        )}

        <div className="flex justify-between">
          <div>
            {currentStep > 1 && (
              <StylizedButton
                variant="outline"
                onClick={() => setCurrentStep(currentStep - 1)}
                iconRight={<ArrowLeft className="w-4 h-4" />}
                withIcon={true}
              >
                Previous
              </StylizedButton>
            )}
          </div>

          <div>
            {currentStep < 4 ? (
              <StylizedButton
                variant="primary"
                onClick={() => setCurrentStep(currentStep + 1)}
                disabled={!isReady || (currentStep === 1 && !tweetUrl)}
                iconRight={<ArrowRight className="w-4 h-4" />}
                withIcon={true}
              >
                Next
              </StylizedButton>
            ) : isLoading ? (
              <button
                disabled
                className="h-9 px-4 bg-background/80 border border-primary/20 text-muted-foreground rounded-md flex items-center justify-center gap-2 text-sm"
              >
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processing...</span>
              </button>
            ) : (
              <StylizedButton
                variant="glow"
                onClick={handleSubmit}
                disabled={!isReady || !tweetUrl}
                iconRight={<CheckCircle2 className="w-4 h-4" />}
                withIcon={true}
              >
                Register IP ({depositAmount} Token)
              </StylizedButton>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
