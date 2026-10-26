```
SELECT
    Brand,
    COUNT(*) FILTER (
        WHERE LOWER(ReturnStatus) IN ('returned', 'exchanged', 'return', 'exchange')
    ) AS returned_or_exchanged_orders,
    COUNT(*) FILTER (
        WHERE LOWER(ReturnStatus) IN ('not returned', 'no return', 'none', 'no')
    ) AS orders_without_returns
FROM Ecommerce
GROUP BY Brand
ORDER BY Brand;
```