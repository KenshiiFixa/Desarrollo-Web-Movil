# Vault escucha con HTTPS en el puerto 8200, con el certificado de la CA local.
listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "/certs/servidor.crt"
  tls_key_file  = "/certs/servidor.key"
}
