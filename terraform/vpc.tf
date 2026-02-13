# --- VPC for RDS ---

resource "aws_vpc" "rds_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name = "rds-vpc"
  }
}

resource "aws_subnet" "rds_subnet1" {
  vpc_id            = aws_vpc.rds_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "eu-west-2a"
  tags = {
    Name = "rds-subnet1"
  }
}

resource "aws_subnet" "rds_subnet2" {
  vpc_id            = aws_vpc.rds_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-2b"
  tags = {
    Name = "rds-subnet2"
  }
}

resource "aws_internet_gateway" "rds_igw" {
  vpc_id = aws_vpc.rds_vpc.id
  tags = {
    Name = "rds-igw"
  }
}

resource "aws_eip" "nat_eip" {
  domain = "vpc"
  tags = {
    Name = "nat-eip"
  }
}

resource "aws_nat_gateway" "nat_gw" {
  allocation_id = aws_eip.nat_eip.id
  subnet_id     = aws_subnet.rds_subnet1.id
  tags = {
    Name = "nat-gw"
  }
}

resource "aws_route_table" "rds_rt" {
  vpc_id = aws_vpc.rds_vpc.id
  route {
    cidr_block     = "0.0.0.0/0"
    gateway_id     = aws_internet_gateway.rds_igw.id
  }
  tags = {
    Name = "rds-rt"
  }
}

resource "aws_route_table_association" "rds_rta1" {
  subnet_id      = aws_subnet.rds_subnet1.id
  route_table_id = aws_route_table.rds_rt.id
}

resource "aws_route_table_association" "rds_rta2" {
  subnet_id      = aws_subnet.rds_subnet2.id
  route_table_id = aws_route_table.rds_rt.id
}

# Security Group for RDS
resource "aws_security_group" "rds_sg" {
  name_prefix = "rds-sg-"
  vpc_id      = aws_vpc.rds_vpc.id
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Open for demo; restrict in production
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# DB Subnet Group
resource "aws_db_subnet_group" "rds_subnet_group" {
  name       = "rds-subnet-group"
  subnet_ids = [aws_subnet.rds_subnet1.id, aws_subnet.rds_subnet2.id]
}