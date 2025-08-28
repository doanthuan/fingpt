GRANT_TYPE = "password"
CLIENT_ID = "bb-tooling-client"

IDENTITY_DOMAIN = (
    "identity.{runtime_name}.{installation_name}.azure.backbaseservices.com"
)
EDGE_DOMAIN = (
    "{user_type}.{runtime_name}.{installation_name}.azure.backbaseservices.com"
)

TOKEN_URL = (
    "https://{identity_domain}/auth/realms/customer/protocol/openid-connect/token"
)
SERVICE_URL = "https://{edge_domain}/api/access-control/client-api/v3/accessgroups/user-context/service-agreements"
USER_CONTEXT_URL = (
    "https://{edge_domain}/api/access-control/client-api/v3/accessgroups/user-context"
)
PRODUCT_SUMMARY_URL = (
    "https://{edge_domain}/api/arrangement-manager/client-api/v2/productsummary"
)
TRANSACTION_MANAGER_URL = (
    "https://{edge_domain}/api/transaction-manager/client-api/v2/transactions"
)

PAYMENT_MANAGER_URL = (
    "https://{edge_domain}/api/payment-order-service/client-api/v2/payment-orders"
)

CONTACT_LIST_URL = "https://{edge_domain}/api/contact-manager/client-api/v2/contacts"
ACCOUNT_DETAIL_URL = "https://{edge_domain}/api/arrangement-manager/client-api/v2/arrangements/{{productId}}"
CARD_LIST_URL = (
    "https://{edge_domain}/api/cards-presentation-service/client-api/v2/cards"
)
COOKIE_KEYS = ["USER_CONTEXT", "ASLBSA", "ASLBSACORS", "XSRF-TOKEN"]

AUTH_TIMEOUT = 600
