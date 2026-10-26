SELECT Brand,
       COUNT(DISTINCT OrderID) FILTER (WHERE ReturnStatus IS NOT NULL AND TRIM(ReturnStatus) <> '' AND LOWER(TRIM(ReturnStatus)) NOT IN ('none','no','not returned','n/a')) AS returned_or_exchanged_orders,
       COUNT(DISTINCT OrderID) FILTER (WHERE ReturnStatus IS NULL OR TRIM(ReturnStatus) = '' OR LOWER(TRIM(ReturnStatus)) IN ('none','no','not returned','n/a')) AS no_return_orders
FROM Ecommerce
GROUP BY Brand
ORDER BY Brand;