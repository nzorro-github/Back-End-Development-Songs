locals {
  app = "${var.project}-song"
  db  = "${var.project}-mongodb"
}

data "kubernetes_service_account" "sa" {
  metadata {
    name      = "${var.project}-service-account"
    namespace = var.environment
  }
}

resource "kubernetes_secret_v1" "mongodb-secret" {
  metadata {
    name      = "${local.db}-secret"
    namespace = var.environment
  }
  data = {
    MONGODB_SERVICE            = "${local.db}-svc"
    MONGODB_PORT               = 27017
  }
}
resource "kubernetes_deployment_v1" "mongodb" {
  metadata {
    name      = "${var.project}-mongodb"
    namespace = var.environment
    labels = {
      app = "${var.project}-db"
      env = var.environment
    }
  }
  depends_on = [kubernetes_secret_v1.mongodb-secret]

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "${var.project}-db"
        env = var.environment
      }
    }

    template {
      metadata {
        labels = {
          app = "${var.project}-db"
          env = var.environment
        }
      }

      spec {
        container {
          image = "docker.io/mongo"
          name  = "mongodb-ctr"

          env_from {
            secret_ref {
              name = kubernetes_secret_v1.mongodb-secret.metadata[0].name
            }
          }

          resources {
            limits = {
              cpu    = "0.5"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "50Mi"
            }
          }
        }
      }
    }
  }
}
###############################################
# MongoDB K8S SERVICE
################################################
resource "kubernetes_service_v1" "mongodb_svc" {
  metadata {
    name      = "${local.db}-svc"
    namespace = var.environment
  }

  spec {
    selector = {
      app = kubernetes_deployment_v1.mongodb.spec[0].template[0].metadata[0].labels.app
      env = kubernetes_deployment_v1.mongodb.spec[0].template[0].metadata[0].labels.env
    }
    type = "ClusterIP"
    port {
      target_port = 27017
      port        = 27017
      protocol    = "TCP"
    }
  }
}
resource "kubernetes_deployment_v1" "song_service" {
  metadata {
    name      = local.app
    namespace = var.environment
    labels = {
      app = local.app
      env = var.environment
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = local.app
        env = var.environment
      }
    }

    template {
      metadata {
        labels = {
          app = local.app
          env = var.environment
        }
      }

      spec {
        container {
          image = var.image
          name  = "${local.app}-cntr"
          env_from {
            secret_ref {
              name = kubernetes_secret_v1.mongodb-secret.metadata[0].name
            }
          }

          resources {
            limits = {
              cpu    = "0.5"
              memory = "512Mi"
            }
            requests = {
              cpu    = "250m"
              memory = "50Mi"
            }
          }
        }
      }
    }
  }
}
###############################################
# Song K8S SERVICE
################################################
resource "kubernetes_service_v1" "song_svc" {
  metadata {
    name      = "${local.app}-svc"
    namespace = var.environment
  }

  spec {
    selector = {
      app = kubernetes_deployment_v1.song_service.spec[0].template[0].metadata[0].labels.app
      env = kubernetes_deployment_v1.song_service.spec[0].template[0].metadata[0].labels.env
    }
    type = "ClusterIP"
    port {
      target_port = var.port
      port        = var.port
      protocol    = "TCP"
    }
  }
}
