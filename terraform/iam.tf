# Optional: IAM role/policy for EKS service accounts (IRSA)
resource "aws_iam_openid_connect_provider" "eks" {
  url = module.eks.cluster_oidc_issuer_url
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.eks_thumbprint.certificates[0].sha1_fingerprint]
}

# We will let the EKS module create node-role automatically; this file is a placeholder
data "tls_certificate" "eks_thumbprint" {
  url = module.eks.cluster_endpoint
  # empty if not available during plan — the EKS module usually handles OIDC creation
}
