resource "aws_db_subnet_group" "default" {
  name       = "${var.project}-${var.environment}-db-subnet-group"
  subnet_ids = module.vpc.private_subnets
  tags = { Name = "${var.project}-db-subnet" }
}

resource "aws_db_instance" "mysql" {
  identifier              = "${var.project}-${var.environment}-mysql"
  engine                  = "mysql"
  engine_version          = "8.0"
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage_gb
  name                    = "educall_db"
  username                = var.db_username
  password                = var.db_password
  skip_final_snapshot     = true
  publicly_accessible     = false
  db_subnet_group_name    = aws_db_subnet_group.default.name
  vpc_security_group_ids  = [aws_security_group.db_sg.id]
  backup_retention_period = 7
  multi_az                = false # change to true for prod HA
  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_security_group" "db_sg" {
  name        = "${var.project}-${var.environment}-db-sg"
  vpc_id      = module.vpc.vpc_id
  description = "Allow app -> DB"
  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"] # restrict to VPC CIDR
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Project = var.project }
}
