-- MySQL dump 10.13  Distrib 5.7.19, for Linux (x86_64)
--
-- Host: pittgrub-dev.ciwlly6ee8ly.us-east-1.rds.amazonaws.com    Database: PittGrub_prod
-- ------------------------------------------------------
-- Server version	5.7.17-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `AccessToken`
--

DROP TABLE IF EXISTS `AccessToken`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `AccessToken` (
  `id` char(32) NOT NULL,
  `user_id` bigint(20) DEFAULT NULL,
  `expires` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `AccessToken_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `AccessToken`
--

LOCK TABLES `AccessToken` WRITE;
/*!40000 ALTER TABLE `AccessToken` DISABLE KEYS */;
/*!40000 ALTER TABLE `AccessToken` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `Event`
--

DROP TABLE IF EXISTS `Event`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Event` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created` datetime NOT NULL,
  `organizer` bigint(20) DEFAULT NULL,
  `organization` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `start_date` datetime NOT NULL,
  `end_date` datetime NOT NULL,
  `details` varchar(500) DEFAULT NULL,
  `servings` int(11) DEFAULT NULL,
  `address` varchar(255) NOT NULL,
  `location` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `organizer` (`organizer`),
  CONSTRAINT `Event_ibfk_1` FOREIGN KEY (`organizer`) REFERENCES `User` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Event`
--

LOCK TABLES `Event` WRITE;
/*!40000 ALTER TABLE `Event` DISABLE KEYS */;
/*!40000 ALTER TABLE `Event` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EventFoodPreference`
--

DROP TABLE IF EXISTS `EventFoodPreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EventFoodPreference` (
  `event_id` bigint(20) NOT NULL,
  `foodpreference_id` bigint(20) NOT NULL,
  PRIMARY KEY (`event_id`,`foodpreference_id`),
  KEY `foodpreference_id` (`foodpreference_id`),
  CONSTRAINT `EventFoodPreference_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `Event` (`id`),
  CONSTRAINT `EventFoodPreference_ibfk_2` FOREIGN KEY (`foodpreference_id`) REFERENCES `FoodPreference` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EventFoodPreference`
--

LOCK TABLES `EventFoodPreference` WRITE;
/*!40000 ALTER TABLE `EventFoodPreference` DISABLE KEYS */;
/*!40000 ALTER TABLE `EventFoodPreference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EventImage`
--

DROP TABLE IF EXISTS `EventImage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EventImage` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `event` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `event` (`event`),
  CONSTRAINT `EventImage_ibfk_1` FOREIGN KEY (`event`) REFERENCES `Event` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EventImage`
--

LOCK TABLES `EventImage` WRITE;
/*!40000 ALTER TABLE `EventImage` DISABLE KEYS */;
/*!40000 ALTER TABLE `EventImage` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EventType`
--

DROP TABLE IF EXISTS `EventType`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EventType` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EventType`
--

LOCK TABLES `EventType` WRITE;
/*!40000 ALTER TABLE `EventType` DISABLE KEYS */;
/*!40000 ALTER TABLE `EventType` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `EventTypeRel`
--

DROP TABLE IF EXISTS `EventTypeRel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `EventTypeRel` (
  `event_id` bigint(20) NOT NULL,
  `event_type_id` bigint(20) NOT NULL,
  PRIMARY KEY (`event_id`,`event_type_id`),
  KEY `event_type_id` (`event_type_id`),
  CONSTRAINT `EventTypeRel_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `Event` (`id`),
  CONSTRAINT `EventTypeRel_ibfk_2` FOREIGN KEY (`event_type_id`) REFERENCES `EventType` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `EventTypeRel`
--

LOCK TABLES `EventTypeRel` WRITE;
/*!40000 ALTER TABLE `EventTypeRel` DISABLE KEYS */;
/*!40000 ALTER TABLE `EventTypeRel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `FoodPreference`
--

DROP TABLE IF EXISTS `FoodPreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `FoodPreference` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `FoodPreference`
--

LOCK TABLES `FoodPreference` WRITE;
/*!40000 ALTER TABLE `FoodPreference` DISABLE KEYS */;
INSERT INTO `FoodPreference` VALUES (1,'Gluten Free','No gluten, which is found in wheat, barley, rye, and oat.'),(2,'Dairy Free','No dairy, which includes any items made with cow\'s milk. This includes milk, butter, cheese, and cream.'),(3,'Vegetarian','No meat, which includes red meat, poultry, and seafood.'),(4,'Vegan','No animal products, includes, but not limited to, dairy (milk products), eggs, meat (red meat, poultry, and seafood), and honey.');
/*!40000 ALTER TABLE `FoodPreference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `User`
--

DROP TABLE IF EXISTS `User`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `User` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `created` datetime NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password` char(75) COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` enum('REFERRAL','REQUESTED','VERIFIED','ACCEPTED') COLLATE utf8mb4_unicode_ci NOT NULL,
  `active` tinyint(1) NOT NULL,
  `disabled` tinyint(1) NOT NULL,
  `admin` tinyint(1) NOT NULL,
  `expo_token` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `login_count` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `User`
--

LOCK TABLES `User` WRITE;
/*!40000 ALTER TABLE `User` DISABLE KEYS */;
/*!40000 ALTER TABLE `User` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserAcceptedEvent`
--

DROP TABLE IF EXISTS `UserAcceptedEvent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserAcceptedEvent` (
  `event_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`event_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `UserAcceptedEvent_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `Event` (`id`),
  CONSTRAINT `UserAcceptedEvent_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserAcceptedEvent`
--

LOCK TABLES `UserAcceptedEvent` WRITE;
/*!40000 ALTER TABLE `UserAcceptedEvent` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserAcceptedEvent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserCheckedInEvent`
--

DROP TABLE IF EXISTS `UserCheckedInEvent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserCheckedInEvent` (
  `event_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`event_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `UserCheckedInEvent_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `Event` (`id`),
  CONSTRAINT `UserCheckedInEvent_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserCheckedInEvent`
--

LOCK TABLES `UserCheckedInEvent` WRITE;
/*!40000 ALTER TABLE `UserCheckedInEvent` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserCheckedInEvent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserFoodPreference`
--

DROP TABLE IF EXISTS `UserFoodPreference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserFoodPreference` (
  `user_id` bigint(20) NOT NULL,
  `foodpreference_id` bigint(20) NOT NULL,
  PRIMARY KEY (`user_id`,`foodpreference_id`),
  KEY `foodpreference_id` (`foodpreference_id`),
  CONSTRAINT `UserFoodPreference_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`),
  CONSTRAINT `UserFoodPreference_ibfk_2` FOREIGN KEY (`foodpreference_id`) REFERENCES `FoodPreference` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserFoodPreference`
--

LOCK TABLES `UserFoodPreference` WRITE;
/*!40000 ALTER TABLE `UserFoodPreference` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserFoodPreference` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserRecommendedEvent`
--

DROP TABLE IF EXISTS `UserRecommendedEvent`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserRecommendedEvent` (
  `event_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`event_id`,`user_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `UserRecommendedEvent_ibfk_1` FOREIGN KEY (`event_id`) REFERENCES `Event` (`id`),
  CONSTRAINT `UserRecommendedEvent_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserRecommendedEvent`
--

LOCK TABLES `UserRecommendedEvent` WRITE;
/*!40000 ALTER TABLE `UserRecommendedEvent` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserRecommendedEvent` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserReferral`
--

DROP TABLE IF EXISTS `UserReferral`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserReferral` (
  `requester` bigint(20) NOT NULL,
  `reference` bigint(20) DEFAULT NULL,
  `status` enum('PENDING','APPROVED','DENIED') COLLATE utf8mb4_unicode_ci NOT NULL,
  `time` datetime NOT NULL,
  PRIMARY KEY (`requester`),
  KEY `reference` (`reference`),
  CONSTRAINT `UserReferral_ibfk_1` FOREIGN KEY (`requester`) REFERENCES `User` (`id`),
  CONSTRAINT `UserReferral_ibfk_2` FOREIGN KEY (`reference`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserReferral`
--

LOCK TABLES `UserReferral` WRITE;
/*!40000 ALTER TABLE `UserReferral` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserReferral` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `UserVerification`
--

DROP TABLE IF EXISTS `UserVerification`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `UserVerification` (
  `code` char(6) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` bigint(20) NOT NULL,
  PRIMARY KEY (`code`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `UserVerification_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `User` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `UserVerification`
--

LOCK TABLES `UserVerification` WRITE;
/*!40000 ALTER TABLE `UserVerification` DISABLE KEYS */;
/*!40000 ALTER TABLE `UserVerification` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2017-10-02 16:32:23
