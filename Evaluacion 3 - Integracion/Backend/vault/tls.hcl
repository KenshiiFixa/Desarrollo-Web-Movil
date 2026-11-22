# Vault en modo desarrollo, pero escuchando con HTTPS en el puerto 8200 con el certificado de la CA local.
# (El listener propio del modo desarrollo queda solo en 127.0.0.1 dentro del contenedor de Vault.)
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/certs/servidor.crt"
  tls_key_file  = "/certs/servidor.key"
}
