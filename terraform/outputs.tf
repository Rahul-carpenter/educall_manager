output "ecr_repository" {
  value = aws_ecr_repository.web.repository_url
}

output "eks_cluster_name" {
  value = module.eks.cluster_id
}

output "kubeconfig" {
  value = module.eks.kubeconfig # note: module may not expose this by default; you can use outputs for cluster endpoint / arn
}

output "rds_endpoint" {
  value = aws_db_instance.mysql.address
  sensitive = false
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
  sensitive = false
}
