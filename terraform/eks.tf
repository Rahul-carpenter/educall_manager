module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = ">= 20.0"

  cluster_name    = "${var.project}-${var.environment}-eks"
  cluster_version = "1.26"   # choose a supported k8s version
  subnets         = module.vpc.private_subnets
  vpc_id          = module.vpc.vpc_id

  node_groups = {
    default = {
      desired_capacity = var.node_desired_capacity
      min_capacity     = 1
      max_capacity     = 3
      instance_type    = var.node_instance_type
      key_name         = null
    }
  }

  manage_aws_auth = true

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}
