📞 EduCall Manager — Production-Ready Lead Management Platform

EduCall Manager is a full-stack, production-grade Lead Management System built for educational agencies to manage calls, agents, bulk leads, email workflows, and reporting.

This repository contains everything required to run EduCall Manager in local development, Docker, and Kubernetes (K8s) environments with Redis + Celery, PostgreSQL, CI/CD, and Terraform provisioning for AWS infrastructure.

🚀 Features
🎯 Core Application

Admin & Agent Role-Based Access

Lead Upload (CSV/XLSX)

Lead Assignment & Tracking

Status Updates (Interested / Not Interested / Pending / Talk Later)

Agent Completion Notification

Bulk Email Sending (All Leads or Per Agent)

Agent Dashboard + Admin Dashboard

Global Search (Leads + Agents)

Auto Database Migrations

⚙️ Production Engineering

Dockerized Flask application

Kubernetes Deployments:

Web Deployment

Celery Worker Deployment

Redis Deployment

Liveness & Readiness Probes

Environment-based configuration via ConfigMap & Secret

External PostgreSQL support

Redis Queue for background processing

Celery Workers for scalable async tasks

🛠 DevOps & CI/CD

Jenkins CI/CD Pipeline

DockerHub Push

Automated Kubernetes Deployment

Rollout strategy with kubectl rollout

Secret & Config handling using Jenkins Credentials

Local Development Mode

☁️ Terraform (Optional for Cloud Deployment)

VPC

Public & Private Subnets

Internet Gateway

NAT Gateway

EKS Cluster

Node Group

Security Groups

IAM roles (EKS, Worker nodes, Jenkins if needed)