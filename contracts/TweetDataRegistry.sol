// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title TweetDataRegistry
 * @notice Stores processed tweet data on Filecoin mainnet
 * @dev Backend writes here after scraping + storing to IPFS/Filecoin
 */
contract TweetDataRegistry {
    address public owner;
    uint256 public tweetCount;
    
    /// @notice Tweet identity information
    struct TweetIdentity {
        bytes32 tweetHash;
        string tweetURL;
        string tweetId;
        string user;
        string handle;
        bool verified;
    }
    
    /// @notice Tweet engagement metrics
    struct TweetMetrics {
        uint256 timestamp;
        uint256 likes;
        uint256 retweets;
        uint256 replies;
        uint256 controversyScore;
        uint256 deletionLikelihood;
    }
    
    /// @notice IPFS and Filecoin storage data
    struct TweetStorage {
        string ipfsScreenshotCID;
        string ipfsDataCID;
        string filecoinRootCID;
        string filecoinDealId;
        string ecosystem;
    }
    
    /// @notice Processing metadata
    struct TweetMeta {
        address submitter;
        address processor;
        uint256 processedAt;
        bool exists;
    }
    
    /// @notice Complete tweet data
    struct TweetData {
        TweetIdentity identity;
        string content;
        TweetMetrics metrics;
        TweetStorage storageData;
        TweetMeta meta;
    }
    
    /// @notice Mapping: tweetHash => TweetData
    mapping(bytes32 => TweetData) private tweets;
    
    /// @notice Array of all tweet hashes for enumeration
    bytes32[] public tweetHashes;
    
    /// @notice Mapping: user handle => their tweet hashes
    mapping(string => bytes32[]) public tweetsByUser;
    
    /// @notice Mapping: ecosystem => tweet hashes
    mapping(string => bytes32[]) public tweetsByEcosystem;
    
    /// @notice Mapping: IPFS CID => tweet hash (for reverse lookup)
    mapping(string => bytes32) public cidToTweetHash;
    
    // Events
    event TweetStored(
        bytes32 indexed tweetHash,
        string tweetURL,
        address indexed submitter,
        address indexed processor,
        string ipfsScreenshotCID,
        string filecoinRootCID
    );
    
    event TweetUpdated(
        bytes32 indexed tweetHash,
        string field,
        string newValue
    );
    
    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }
    
    constructor() {
        owner = msg.sender;
    }
    
    /**
     * @notice Store processed tweet data
     */
    function storeTweet(
        TweetIdentity calldata identity,
        string calldata content,
        TweetMetrics calldata metrics,
        TweetStorage calldata storageData,
        address submitter
    ) external onlyOwner {
        require(!tweets[identity.tweetHash].meta.exists, "Tweet already stored");
        require(bytes(identity.tweetURL).length > 0, "Invalid tweet URL");
        
        TweetData storage t = tweets[identity.tweetHash];
        
        t.identity = identity;
        t.content = content;
        t.metrics = metrics;
        t.storageData = storageData;
        t.meta.submitter = submitter;
        t.meta.processor = msg.sender;
        t.meta.processedAt = block.timestamp;
        t.meta.exists = true;
        
        tweetHashes.push(identity.tweetHash);
        tweetsByUser[identity.handle].push(identity.tweetHash);
        tweetsByEcosystem[storageData.ecosystem].push(identity.tweetHash);
        
        if (bytes(storageData.ipfsScreenshotCID).length > 0) {
            cidToTweetHash[storageData.ipfsScreenshotCID] = identity.tweetHash;
        }
        if (bytes(storageData.ipfsDataCID).length > 0) {
            cidToTweetHash[storageData.ipfsDataCID] = identity.tweetHash;
        }
        if (bytes(storageData.filecoinRootCID).length > 0) {
            cidToTweetHash[storageData.filecoinRootCID] = identity.tweetHash;
        }
        
        tweetCount++;
        
        emit TweetStored(
            identity.tweetHash,
            identity.tweetURL,
            submitter,
            msg.sender,
            storageData.ipfsScreenshotCID,
            storageData.filecoinRootCID
        );
    }
    
    /**
     * @notice Get tweet by hash
     */
    function getTweet(bytes32 tweetHash) 
        external 
        view 
        returns (TweetData memory) 
    {
        require(tweets[tweetHash].meta.exists, "Tweet not found");
        return tweets[tweetHash];
    }
    
    /**
     * @notice Get tweet by URL
     */
    function getTweetByURL(string calldata tweetURL) 
        external 
        view 
        returns (TweetData memory) 
    {
        bytes32 hash = keccak256(abi.encodePacked(tweetURL));
        require(tweets[hash].meta.exists, "Tweet not found");
        return tweets[hash];
    }
    
    /**
     * @notice Get tweet by any CID
     */
    function getTweetByCID(string calldata cid) 
        external 
        view 
        returns (TweetData memory) 
    {
        bytes32 hash = cidToTweetHash[cid];
        require(tweets[hash].meta.exists, "Tweet not found");
        return tweets[hash];
    }
    
    /**
     * @notice Get tweets by user (paginated)
     */
    function getTweetsByUser(string calldata handle, uint256 offset, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        return getPaginatedHashes(tweetsByUser[handle], offset, limit);
    }
    
    /**
     * @notice Get tweets by ecosystem (paginated)
     */
    function getTweetsByEcosystem(string calldata ecosystem, uint256 offset, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        return getPaginatedHashes(tweetsByEcosystem[ecosystem], offset, limit);
    }
    
    /**
     * @notice Get all tweet hashes (paginated)
     */
    function getAllTweetHashes(uint256 offset, uint256 limit)
        external
        view
        returns (bytes32[] memory)
    {
        return getPaginatedHashes(tweetHashes, offset, limit);
    }
    
    /**
     * @notice Internal pagination helper
     */
    function getPaginatedHashes(bytes32[] storage hashes, uint256 offset, uint256 limit)
        internal
        view
        returns (bytes32[] memory)
    {
        uint256 end = offset + limit;
        if (end > hashes.length) {
            end = hashes.length;
        }
        if (offset >= hashes.length) {
            return new bytes32[](0);
        }
        
        bytes32[] memory result = new bytes32[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = hashes[i];
        }
        
        return result;
    }
    
    /**
     * @notice Get total count
     */
    function getTotalCount() external view returns (uint256) {
        return tweetCount;
    }
    
    /**
     * @notice Get user tweet count
     */
    function getUserTweetCount(string calldata handle) external view returns (uint256) {
        return tweetsByUser[handle].length;
    }
    
    /**
     * @notice Get ecosystem tweet count
     */
    function getEcosystemTweetCount(string calldata ecosystem) external view returns (uint256) {
        return tweetsByEcosystem[ecosystem].length;
    }
    
    /**
     * @notice Update CID fields if needed
     */
    function updateCIDs(
        bytes32 tweetHash,
        string calldata ipfsScreenshotCID,
        string calldata ipfsDataCID,
        string calldata filecoinRootCID,
        string calldata filecoinDealId
    ) external onlyOwner {
        require(tweets[tweetHash].meta.exists, "Tweet not found");
        
        TweetData storage t = tweets[tweetHash];
        
        if (bytes(ipfsScreenshotCID).length > 0) {
            t.storageData.ipfsScreenshotCID = ipfsScreenshotCID;
            cidToTweetHash[ipfsScreenshotCID] = tweetHash;
        }
        if (bytes(ipfsDataCID).length > 0) {
            t.storageData.ipfsDataCID = ipfsDataCID;
            cidToTweetHash[ipfsDataCID] = tweetHash;
        }
        if (bytes(filecoinRootCID).length > 0) {
            t.storageData.filecoinRootCID = filecoinRootCID;
            cidToTweetHash[filecoinRootCID] = tweetHash;
        }
        if (bytes(filecoinDealId).length > 0) {
            t.storageData.filecoinDealId = filecoinDealId;
        }
        
        emit TweetUpdated(tweetHash, "CIDs", "updated");
    }
    
    /**
     * @notice Check if tweet exists
     */
    function exists(bytes32 tweetHash) external view returns (bool) {
        return tweets[tweetHash].meta.exists;
    }
    
    /**
     * @notice Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }
}