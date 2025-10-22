// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract IP_Deposit {
    address public owner;

    /// @notice Configuration for a new collection
    struct CollectionConfig {
        string handle;
        uint256 mintPrice;
        uint256 maxSupply;
        address royaltyReceiver;
        uint96  royaltyBP;
    }

    /// @notice Full license‐terms configuration
    struct LicenseTermsConfig {
        uint256 defaultMintingFee;
        address currency;
        address royaltyPolicy;
        bool    transferable;
        uint256 expiration;
        bool    commercialUse;
        bool    commercialAttribution;
        uint256 commercialRevShare;
        uint256 commercialRevCeiling;
        bool    derivativesAllowed;
        bool    derivativesAttribution;
        bool    derivativesApproval;
        bool    derivativesReciprocal;
        uint256 derivativeRevCeiling;
        string  uri;
    }

    /// @notice Parameters for minting license tokens
    struct LicenseMintParams {
        uint256 licenseTermsId;
        address licensorIpId;
        address receiver;
        uint256 amount;
        uint256 maxMintingFee;
        uint256 maxRevenueShare;
    }

    /// @notice Any extra co‐creators
    struct CoCreator {
        string name;
        address wallet;
    }

    /// @notice Everything we’d like to store per‐tweet deposit
    struct DepositRecord {
        address              depositor;
        address              recipient;
        string               validation;
        bytes                proof;
        address              collectionAddress;
        CollectionConfig     collectionConfig;
        bytes32              tweetHash;
        LicenseTermsConfig   licenseTermsConfig;
        LicenseMintParams    licenseMintParams;
        CoCreator[]          coCreators;
    }

    mapping(bytes32 => DepositRecord) private _deposits;

    /// @notice Emitted when a deposit is processed, with every parameter from the trigger
    event DepositProcessed(
        uint256              indexed ipAmount,
        bytes32              indexed tweetHash,
        address              indexed depositor,
        address                     recipient,
        string                      validation,
        bytes                       proof,
        address                     collectionAddress,
        CollectionConfig            collectionConfig,
        bytes32                     tweetHashOut,
        LicenseTermsConfig          licenseTermsConfig,
        LicenseMintParams           licenseMintParams,
        CoCreator[]                 coCreators
    );

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    /// @param tweetHash            keccak256(abi.encodePacked(tweetURL))
    /// @param collectionAddress    zero‐address if you’ll deploy off‐chain
    function depositIP(
        address                    recipient,
        string    calldata         validation,
        bytes     calldata         proof,
        address                    collectionAddress,
        CollectionConfig calldata  collectionConfig,
        bytes32                    tweetHash,
        LicenseTermsConfig calldata licenseTermsConfig,
        LicenseMintParams calldata  licenseMintParams,
        CoCreator[] calldata       coCreators
    ) external payable {
        require(msg.value > 0, "Must send IP");
        require(recipient != address(0), "Invalid recipient");
        require(_deposits[tweetHash].depositor == address(0), "Already deposited");

        DepositRecord storage r = _deposits[tweetHash];
        r.depositor           = msg.sender;
        r.recipient           = recipient;
        r.validation          = validation;
        r.proof               = proof;
        r.collectionAddress   = collectionAddress;
        r.collectionConfig    = collectionConfig;
        r.tweetHash           = tweetHash;
        r.licenseTermsConfig  = licenseTermsConfig;
        r.licenseMintParams   = licenseMintParams;
        for (uint i = 0; i < coCreators.length; i++) {
            r.coCreators.push(coCreators[i]);
        }

        emit DepositProcessed(
            msg.value,
            tweetHash,
            msg.sender,
            recipient,
            validation,
            proof,
            collectionAddress,
            collectionConfig,
            tweetHash,
            licenseTermsConfig,
            licenseMintParams,
            coCreators
        );
    }

    /// @notice Look up all parameters by the pre‐computed tweetHash
    function getByTweetHash(bytes32 tweetHash)
        external
        view
        returns (DepositRecord memory)
    {
        require(_deposits[tweetHash].depositor != address(0), "Not found");
        return _deposits[tweetHash];
    }

    event ValidationUpdated(bytes32 indexed tweetHash, string newValidation);
    function updateValidation(bytes32 tweetHash, string calldata newValidation)
        external onlyOwner
    {
        require(_deposits[tweetHash].depositor != address(0), "Not found");
        _deposits[tweetHash].validation = newValidation;
        emit ValidationUpdated(tweetHash, newValidation);
    }

    function withdrawFunds() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds");
        (bool success,) = owner.call{value: balance}("");
        require(success, "Transfer failed");
    }

    receive() external payable {}
}