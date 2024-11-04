;; game-rewards-enhanced.clar
(define-constant ERR_INSUFFICIENT_FUNDS (err u1))
(define-constant ERR_UNAUTHORIZED (err u2))
(define-constant ERR_INVALID_PARAMS (err u3))

;; Data variables
(define-data-var reward-pool uint u0)
(define-data-var admin principal tx-sender)
(define-data-var paused bool false)

;; Maps
(define-map player-rewards principal uint)
(define-map player-items {player: principal, item-id: uint} 
    {rarity: (string-ascii 20), boost: uint, durability: uint})
(define-map daily-quest-counts {player: principal, day: uint} uint)

;; NFT management
(define-non-fungible-token game-items uint)

;; Administrative functions
(define-public (set-admin (new-admin principal))
    (begin
        (asserts! (is-eq tx-sender (var-get admin)) ERR_UNAUTHORIZED)
        (var-set admin new-admin)
        (ok true)))

(define-public (pause-game)
    (begin
        (asserts! (is-eq tx-sender (var-get admin)) ERR_UNAUTHORIZED)
        (var-set paused true)
        (ok true)))

(define-public (resume-game)
    (begin
        (asserts! (is-eq tx-sender (var-get admin)) ERR_UNAUTHORIZED)
        (var-set paused false)
        (ok true)))

;; Enhanced reward claiming with daily limits
(define-public (claim-reward (player principal) (amount uint))
    (begin
        (asserts! (not (var-get paused)) ERR_UNAUTHORIZED)
        (asserts! (>= (var-get reward-pool) amount) ERR_INSUFFICIENT_FUNDS)
        
        ;; Get current day number (block height / 144 blocks per day)
        (let ((current-day (/ block-height u144))
              (daily-count (default-to u0 
                (map-get? daily-quest-counts 
                    {player: player, day: current-day}))))
            
            ;; Check daily limit
            (asserts! (< daily-count u10) ERR_INVALID_PARAMS)
            
            ;; Update daily count
            (map-set daily-quest-counts 
                {player: player, day: current-day}
                (+ daily-count u1))
            
            ;; Update reward pool and player rewards
            (var-set reward-pool (- (var-get reward-pool) amount))
            (map-set player-rewards player 
                (+ (default-to u0 (map-get? player-rewards player)) amount))
            
            (ok true))))

;; NFT minting and management
(define-public (mint-item (recipient principal) (item-id uint) 
               (rarity (string-ascii 20)) (boost uint))
    (begin
        (asserts! (not (var-get paused)) ERR_UNAUTHORIZED)
        (asserts! (is-eq tx-sender (var-get admin)) ERR_UNAUTHORIZED)
        
        ;; Mint NFT
        (nft-mint? game-items item-id recipient)
        
        ;; Store item properties
        (map-set player-items 
            {player: recipient, item-id: item-id}
            {rarity: rarity, boost: boost, durability: u100})
            
        (ok true)))

;; Enhanced withdrawal with security checks
(define-public (withdraw-rewards (amount uint))
    (let ((current-balance (default-to u0 (map-get? player-rewards tx-sender))))
        (begin
            (asserts! (not (var-get paused)) ERR_UNAUTHORIZED)
            (asserts! (>= current-balance amount) ERR_INSUFFICIENT_FUNDS)
            
            ;; Implement rate limiting
            (asserts! (< amount u1000000) ERR_INVALID_PARAMS) ;; Max 0.01 BTC per withdrawal
            
            (map-set player-rewards tx-sender (- current-balance amount))
            
            ;; Implement actual BTC transfer logic here with security checks
            ;; This would involve integration with a Bitcoin bridge or similar mechanism
            
            (ok true))))

;; Read-only functions
(define-read-only (get-player-rewards (player principal))
    (ok (default-to u0 (map-get? player-rewards player))))

(define-read-only (get-item-details (player principal) (item-id uint))
    (ok (map-get? player-items {player: player, item-id: item-id})))

(define-read-only (get-daily-quest-count (player principal))
    (let ((current-day (/ block-height u144)))
        (ok (default-to u0 
            (map-get? daily-quest-counts 
                {player: player, day: current-day})))))