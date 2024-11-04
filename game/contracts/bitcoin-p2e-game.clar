;; game-rewards.clar
(define-data-var reward-pool uint u0)
(define-map player-rewards principal uint)

(define-public (initialize-reward-pool (amount uint))
    (begin
        (var-set reward-pool amount)
        (ok true)))

(define-public (claim-reward (player principal) (amount uint))
    (begin
        (asserts! (>= (var-get reward-pool) amount) (err u1))
        (var-set reward-pool (- (var-get reward-pool) amount))
        (map-set player-rewards player 
            (+ (default-to u0 (map-get? player-rewards player)) amount))
        (ok true)))

(define-read-only (get-player-rewards (player principal))
    (ok (default-to u0 (map-get? player-rewards player))))

(define-public (withdraw-rewards (amount uint))
    (let ((current-balance (default-to u0 (map-get? player-rewards tx-sender))))
        (asserts! (>= current-balance amount) (err u2))
        (map-set player-rewards tx-sender (- current-balance amount))
        ;; Implement actual BTC transfer logic here
        (ok true)))