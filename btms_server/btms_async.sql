-- phpMyAdmin SQL Dump
-- version 4.5.0.2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Erstellungszeit: 13. Dez 2015 um 23:33
-- Server-Version: 10.0.17-MariaDB
-- PHP-Version: 5.6.14

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Datenbank: `btms`
--

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_categories`
--

CREATE TABLE `btms_categories` (
  `id` int(11) NOT NULL,
  `name` varchar(80) COLLATE latin1_german1_ci NOT NULL,
  `description` text COLLATE latin1_german1_ci NOT NULL,
  `event_id` int(40) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_categories`
--

INSERT INTO `btms_categories` (`id`, `name`, `description`, `event_id`) VALUES
(1, 'Gruft - Kat I', 'Nummerrierte Logen 1 - 16', 1),
(2, 'Kategorie II', 'Freie Plaetze links und rechts vorne', 1),
(3, 'Kategorie III', 'Freie Plaetze links und rechts hinten', 1),
(4, 'Loge - Kat  I', 'Nummerrierte Logen 1 - 17', 2),
(5, 'Freie - Kat II', 'Freie Plaetze links und rechts vorne', 2),
(6, 'Freie - Kat III', 'Freie Plaetze links und rechts hinten', 2);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_counter`
--

CREATE TABLE `btms_counter` (
  `id` int(30) NOT NULL,
  `name` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `event_id` int(30) NOT NULL,
  `date` date NOT NULL,
  `time` time NOT NULL,
  `amount` int(5) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_counter`
--

INSERT INTO `btms_counter` (`id`, `name`, `event_id`, `date`, `time`, `amount`) VALUES
(1, '', 1, '2015-09-04', '19:00:00', 1030),
(2, '', 1, '2015-09-04', '23:22:00', 1000),
(3, '', 2, '2015-09-15', '16:00:00', 1149),
(4, '', 2, '2015-09-17', '16:00:00', 1000);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_events`
--

CREATE TABLE `btms_events` (
  `id` int(30) NOT NULL,
  `ref` int(40) NOT NULL,
  `title` text COLLATE latin1_german1_ci NOT NULL,
  `description` text COLLATE latin1_german1_ci NOT NULL,
  `date_start` varchar(10) COLLATE latin1_german1_ci NOT NULL,
  `date_end` varchar(10) COLLATE latin1_german1_ci NOT NULL,
  `date_day` varchar(10) COLLATE latin1_german1_ci NOT NULL,
  `start_times` text COLLATE latin1_german1_ci NOT NULL,
  `venue_id` int(11) NOT NULL,
  `reg_date_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user_id` int(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_events`
--

INSERT INTO `btms_events` (`id`, `ref`, `title`, `description`, `date_start`, `date_end`, `date_day`, `start_times`, `venue_id`, `reg_date_time`, `user_id`) VALUES
(1, 0, 'ZDH Berlin', 'Zirkus des Horrors in Berlin', '2016-03-10', '2016-04-24', '0000-00-00', '', 1, '2015-02-02 21:49:15', 1),
(2, 0, 'WZ Karlsruhe', 'WZ Karlsruhe', '2015-12-18', '2016-01-06', '0000-00-00', '', 20, '2015-02-02 21:52:44', 1),
(3, 1, '', '', '0000-00-00', '0000-00-00', '2016-03-10', '1;19:00,2;23:22', 0, '2015-02-16 20:16:11', 0),
(4, 1, '', '', '0000-00-00', '0000-00-00', '2016-03-11', '1;19:00,2;22:00,3;23:00', 0, '2015-02-16 23:12:39', 0),
(5, 2, '', '', '0000-00-00', '0000-00-00', '2015-12-18', '1;16:00,2;17:22', 0, '2015-02-23 23:50:37', 0),
(6, 2, '', '', '0000-00-00', '0000-00-00', '2015-12-19', '1;16:30,2;17:30', 0, '2015-02-23 23:50:37', 0),
(7, 2, '', '', '0000-00-00', '0000-00-00', '2015-12-20', '1;17:00,2;18:30', 0, '2015-02-23 23:52:41', 0);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_items`
--

CREATE TABLE `btms_items` (
  `id` int(11) NOT NULL,
  `title` varchar(80) COLLATE latin1_german1_ci NOT NULL,
  `description` text COLLATE latin1_german1_ci NOT NULL,
  `event_id` int(11) NOT NULL,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_items`
--

INSERT INTO `btms_items` (`id`, `title`, `description`, `event_id`, `date`, `user`) VALUES
(1, 'P. Heft', 'ZDH Programmheft', 1, '2015-04-30 19:15:27', 1),
(2, 'S. Waren', 'ZDH Leckereien', 2, '2015-04-30 19:16:37', 1);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_journal`
--

CREATE TABLE `btms_journal` (
  `id` int(40) NOT NULL,
  `tid` bigint(40) NOT NULL,
  `event_id` int(11) NOT NULL,
  `account` int(4) NOT NULL,
  `debit` decimal(40,2) NOT NULL,
  `credit` decimal(40,2) NOT NULL,
  `user_id` int(40) NOT NULL,
  `reg_date_time` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_journal`
--

INSERT INTO `btms_journal` (`id`, `tid`, `event_id`, `account`, `debit`, `credit`, `user_id`, `reg_date_time`) VALUES
(1, 2147483647, 0, 0, '0.00', '0.00', 0, NULL),
(2, 2147483647, 0, 0, '0.00', '0.00', 0, '2015-10-17 19:13:48'),
(3, 2147483647, 0, 0, '0.00', '0.00', 1, '2015-10-17 19:21:15'),
(4, 2147483647, 0, 0, '0.00', '0.00', 1, '2015-10-17 19:22:11'),
(5, 2147483647, 0, 0, '0.00', '0.00', 1, '2015-10-17 20:37:42'),
(6, 2147483647, 0, 0, '0.00', '0.00', 1, '2015-10-17 20:38:33'),
(7, 120150904190014131, 0, 0, '0.00', '0.00', 1, '2015-10-17 20:39:26'),
(8, 120150904190014131, 0, 0, '0.00', '0.00', 1, '2015-10-17 20:41:19'),
(9, 120150904190014149, 0, 0, '0.00', '0.00', 1, '2015-10-17 20:44:42'),
(10, 120150904190014156, 1, 0, '0.00', '0.00', 1, '2015-10-17 20:46:22'),
(11, 120150904190014156, 1, 0, '0.00', '0.00', 1, '2015-10-17 20:47:48'),
(12, 120150904190014156, 1, 0, '0.00', '0.00', 1, '2015-10-17 20:48:21'),
(13, 120150904190014156, 1, 0, '0.00', '0.00', 1, '2015-10-17 20:48:46'),
(14, 120150904190014164, 1, 1000, '0.00', '0.00', 1, '2015-10-17 20:49:43'),
(15, 120150904190014164, 1, 1000, '0.00', '0.00', 1, '2015-10-17 22:51:10'),
(16, 120150904190014172, 1, 1000, '140.00', '0.00', 1, '2015-10-17 22:57:47'),
(17, 120150904190014180, 1, 1000, '105.00', '0.00', 4, '2015-10-17 22:59:42'),
(18, 120150904190014198, 1, 1000, '105.00', '0.00', 1, '2015-10-17 23:03:12'),
(19, 120150904190014206, 1, 1000, '105.00', '0.00', 1, '2015-10-17 23:06:46'),
(20, 120150904190014206, 1, 1000, '151.00', '0.00', 1, '2015-10-17 23:07:10'),
(21, 120150904190010006, 1, 1000, '183.00', '0.00', 1, '2015-10-17 23:09:25'),
(22, 120150904190010006, 1, 1000, '140.00', '0.00', 1, '2015-10-17 23:45:30'),
(23, 120150904190010014, 1, 1000, '35.00', '0.00', 1, '2015-10-17 23:48:08'),
(24, 120150904190010022, 1, 1000, '105.00', '0.00', 1, '2015-10-17 23:50:55'),
(25, 120150904190010022, 1, 1000, '70.00', '0.00', 1, '2015-10-17 23:52:38'),
(26, 120150904190010030, 1, 1000, '70.00', '0.00', 1, '2015-10-17 23:54:06'),
(27, 120150904190010048, 1, 1000, '140.00', '0.00', 1, '2015-10-17 23:58:50'),
(28, 120150904190010048, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:03:00'),
(29, 120150904190010048, 1, 1000, '140.00', '0.00', 1, '2015-10-18 00:03:10'),
(30, 120150904190010055, 1, 1000, '35.00', '0.00', 1, '2015-10-18 00:05:57'),
(31, 120150904190010055, 1, 1000, '35.00', '0.00', 1, '2015-10-18 00:06:35'),
(32, 120150904190010063, 1, 1000, '35.00', '0.00', 1, '2015-10-18 00:13:06'),
(33, 120150904190010071, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:19:54'),
(34, 120150904190010089, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:23:01'),
(35, 120150904190010097, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:23:31'),
(36, 120150905220010007, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:26:43'),
(37, 220150915160010006, 2, 1000, '90.00', '0.00', 1, '2015-10-18 00:28:32'),
(38, 120150904190010105, 1, 1000, '14720.00', '0.00', 1, '2015-10-18 00:31:15'),
(39, 120150904190010113, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:33:50'),
(40, 120150904190010121, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:34:36'),
(41, 120150904190010139, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:38:21'),
(42, 120150904190010147, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:39:09'),
(43, 120150904190010154, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:39:27'),
(44, 120150904190010162, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:40:16'),
(45, 120150904232210002, 1, 1000, '70.00', '0.00', 1, '2015-10-18 00:49:27'),
(46, 120150904190010196, 1, 1000, '210.00', '0.00', 1, '2015-10-18 01:05:29'),
(47, 120150904190010220, 1, 1000, '197.00', '0.00', 1, '2015-10-18 01:10:08'),
(48, 120150904190010006, 1, 1000, '46.00', '0.00', 1, '2015-10-18 01:24:32'),
(49, 120150904232210002, 1, 1000, '13400.00', '0.00', 1, '2015-10-18 01:24:55'),
(50, 120150904190010014, 1, 1000, '70.00', '0.00', 1, '2015-10-18 01:28:35'),
(51, 120150904190010022, 1, 1000, '70.00', '0.00', 1, '2015-10-18 01:39:15'),
(52, 120150904190010055, 1, 1000, '140.00', '0.00', 1, '2015-10-18 13:01:32'),
(53, 120150904190010295, 1, 1000, '46.00', '0.00', 1, '2015-10-18 20:34:59'),
(54, 220150915160010022, 2, 1000, '71.00', '0.00', 1, '2015-10-19 21:44:52'),
(55, 220150915160010030, 2, 1000, '50.00', '0.00', 1, '2015-10-19 21:46:15'),
(56, 220150915160010089, 2, 1000, '45.00', '0.00', 1, '2015-10-19 22:49:35'),
(57, 220150915160010097, 2, 1000, '90.00', '0.00', 1, '2015-10-19 22:51:41'),
(58, 220150915160010121, 2, 1000, '20.00', '0.00', 1, '2015-10-19 23:29:49'),
(59, 220150915160010154, 2, 1000, '260.00', '0.00', 1, '2015-10-19 23:48:16'),
(60, 220150915160010238, 2, 1000, '1502.50', '0.00', 1, '2015-10-20 00:17:05'),
(61, 220150915160010253, 2, 1000, '540.00', '0.00', 1, '2015-10-20 00:57:12'),
(62, 220150915160010279, 2, 1000, '540.00', '0.00', 1, '2015-10-20 01:42:02'),
(63, 220150915160010295, 2, 1000, '20.00', '0.00', 1, '2015-10-20 01:52:50'),
(64, 220150915160010303, 2, 1000, '180.00', '0.00', 1, '2015-10-20 20:04:15'),
(65, 220150915160010329, 2, 1000, '26.00', '0.00', 1, '2015-10-20 20:04:54'),
(66, 220150915160010378, 2, 1000, '180.00', '0.00', 1, '2015-10-21 00:53:22'),
(67, 220150915160010386, 2, 1000, '180.00', '0.00', 1, '2015-10-21 00:56:15'),
(68, 220150915160010394, 2, 1000, '360.00', '0.00', 4, '2015-10-21 00:57:45'),
(69, 220150915160010493, 2, 1000, '180.00', '0.00', 4, '2015-10-22 19:25:29'),
(70, 220150915160010535, 2, 1000, '716.00', '0.00', 1, '2015-10-23 01:07:35'),
(71, 220150915160010543, 2, 1000, '2.50', '0.00', 1, '2015-10-23 01:10:18'),
(72, 220150915160010550, 2, 1000, '260.00', '0.00', 1, '2015-10-23 01:12:11'),
(73, 220150915160010568, 2, 1000, '180.00', '0.00', 4, '2015-10-23 01:15:47'),
(74, 220150915160010733, 2, 1000, '540.00', '0.00', 1, '2015-10-23 03:00:07'),
(75, 220150915160010741, 2, 1000, '180.00', '0.00', 4, '2015-10-23 03:12:57'),
(76, 220150915160010774, 2, 1000, '200.00', '0.00', 1, '2015-10-23 16:23:54'),
(77, 220150915160010790, 2, 1000, '149.00', '0.00', 1, '2015-10-23 16:52:20'),
(78, 220150915160010808, 2, 1000, '149.00', '0.00', 1, '2015-10-23 16:53:51'),
(79, 220150915160010832, 2, 1000, '225.00', '0.00', 1, '2015-10-23 16:56:25'),
(80, 220150915160010857, 2, 1000, '315.00', '0.00', 1, '2015-10-23 16:57:30'),
(81, 220150915160010865, 2, 1000, '282.00', '0.00', 1, '2015-10-23 16:58:03'),
(82, 220150915160010881, 2, 1000, '228.00', '0.00', 1, '2015-10-23 17:02:24'),
(83, 220150915160010899, 2, 1000, '495.00', '0.00', 4, '2015-10-23 17:03:12'),
(84, 220150915160010907, 2, 1000, '45.00', '0.00', 4, '2015-10-23 17:04:42'),
(85, 220150915160010915, 2, 1000, '91.00', '0.00', 1, '2015-10-23 17:10:09'),
(86, 220150915160010923, 2, 1000, '48.00', '0.00', 1, '2015-10-23 17:10:46'),
(87, 220150915160010931, 2, 1000, '22.00', '0.00', 1, '2015-10-23 17:13:01'),
(88, 220150915160010949, 2, 1000, '225.00', '0.00', 1, '2015-10-23 17:14:20'),
(89, 220150915160011251, 2, 1000, '1080.00', '0.00', 1, '2015-10-24 02:14:52'),
(90, 220150915160011277, 2, 1000, '200.00', '0.00', 1, '2015-10-24 02:17:24'),
(91, 220150915160011269, 2, 1000, '14680.00', '0.00', 4, '2015-10-24 02:18:15'),
(92, 220150915160011285, 2, 1000, '135.00', '0.00', 4, '2015-10-24 02:21:36'),
(93, 220150915160011293, 2, 1000, '450.00', '0.00', 1, '2015-10-24 02:41:09'),
(94, 220150915160011301, 2, 1000, '45.00', '0.00', 1, '2015-10-24 02:41:20'),
(95, 220150915160011319, 2, 1000, '22.50', '0.00', 1, '2015-10-24 02:44:13'),
(96, 220150915160011350, 2, 1000, '386.00', '0.00', 1, '2015-10-24 02:57:46'),
(97, 220150915160011376, 2, 1000, '219.50', '0.00', 1, '2015-10-24 03:02:07'),
(98, 220150915160011384, 2, 1000, '0.00', '0.00', 1, '2015-10-24 03:02:20'),
(99, 220150915160011392, 2, 1000, '37.00', '0.00', 1, '2015-10-24 03:07:07'),
(100, 220150915160011459, 2, 1000, '180.00', '0.00', 1, '2015-10-24 14:27:21'),
(101, 220150915160011467, 2, 1000, '135.00', '0.00', 1, '2015-10-24 14:27:59'),
(102, 220150915160011475, 2, 1000, '135.00', '0.00', 1, '2015-10-24 14:29:19'),
(103, 220150915160011483, 2, 1000, '135.00', '0.00', 1, '2015-10-24 14:34:17'),
(104, 220150915160011491, 2, 1000, '90.00', '0.00', 1, '2015-10-24 16:59:34');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_prices`
--

CREATE TABLE `btms_prices` (
  `id` int(11) NOT NULL,
  `name` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `description` text COLLATE latin1_german1_ci NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `currency` varchar(10) COLLATE latin1_german1_ci NOT NULL,
  `cat_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `event_id` int(11) NOT NULL,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `user` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_prices`
--

INSERT INTO `btms_prices` (`id`, `name`, `description`, `price`, `currency`, `cat_id`, `item_id`, `event_id`, `date`, `user`) VALUES
(1, 'Normal', 'ZDH Gruft Kat 1', '35.00', 'EUR', 1, 0, 1, '2015-04-30 18:52:06', 1),
(2, 'Erm.', 'ZDH Gruft Kat 1', '30.00', 'EUR', 1, 0, 1, '2015-04-30 18:55:53', 1),
(3, 'Gruppe', 'ZDH Gruft Kat 1', '27.00', 'EUR', 1, 0, 1, '2015-05-01 14:47:31', 1),
(4, 'Sonder', 'ZDH Gruft Kat 1', '25.00', 'EUR', 1, 0, 1, '2015-05-01 14:47:31', 1),
(5, 'Super', 'ZDH Gruft Kat 1', '20.00', 'EUR', 1, 0, 1, '2015-05-01 14:49:07', 1),
(6, 'AKT15', 'ZDH Gruft Kat 1', '20.00', 'EUR', 1, 0, 1, '2015-05-01 14:49:07', 1),
(7, 'Norm.', 'ZDH Kategorie II', '26.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(8, 'Erm.', 'ZDH Kategorie II', '23.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(9, 'Grp.', 'ZDH Kategorie II', '22.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(10, 'Sond.', 'ZDH Kategorie II', '20.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(11, 'Sup.', 'ZDH Kategorie II', '10.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(12, 'Akt15', 'ZDH Kategorie II', '15.00', 'EUR', 2, 0, 1, '2015-05-01 14:52:50', 1),
(13, 'Norm.', 'ZDH Kategorie III', '20.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(14, 'Erm.', 'ZDH Kategorie III', '15.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(15, 'Grp.', 'ZDH Kategorie III', '14.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(16, 'Sond.', 'ZDH Kategorie III', '13.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(17, 'Sup.', 'ZDH Kategorie III', '10.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(18, 'AKT13', 'ZDH Kategorie III', '15.00', 'EUR', 3, 0, 1, '2015-05-01 14:55:48', 1),
(19, 'ZDH Programmheft', '', '4.00', 'EUR', 0, 1, 1, '2015-05-01 14:56:49', 1),
(20, 'ZDH Suesswaren', '', '2.50', 'EUR', 0, 2, 2, '2015-05-01 14:57:24', 1),
(21, 'Frei', 'ZDH Gruft Kat 1', '0.00', 'EUR', 1, 0, 1, '2015-09-23 19:05:57', 1),
(22, 'Frei', 'ZDH Kategorie II', '0.00', 'EUR', 2, 0, 1, '2015-09-23 19:06:15', 1),
(23, 'Norm.', 'Loge Kat 1', '45.00', 'EUR', 4, 0, 2, '2015-09-25 01:15:41', 1),
(24, 'Erm.', 'Loge Kat 1', '30.00', 'EUR', 4, 0, 2, '2015-04-30 18:55:53', 1),
(25, 'Grp.', 'Loge Kat 1', '27.00', 'EUR', 4, 0, 2, '2015-05-01 14:47:31', 1),
(26, 'Sond.', 'Loge Kat 1', '25.00', 'EUR', 4, 0, 2, '2015-05-01 14:47:31', 1),
(27, 'Sup.', 'Loge Kat 1', '20.00', 'EUR', 4, 0, 2, '2015-05-01 14:49:07', 1),
(28, 'AKT15', 'Loge Kat 1', '20.00', 'EUR', 4, 0, 2, '2015-05-01 14:49:07', 1),
(29, 'Frei', 'Loge Kat 1', '0.00', 'EUR', 4, 0, 2, '2015-09-23 19:05:57', 1),
(30, 'Norm.', 'Kategorie II', '26.00', 'EUR', 5, 0, 2, '2015-05-01 14:52:50', 1),
(31, 'Erm.', 'Kategorie II', '23.00', 'EUR', 5, 0, 2, '2015-05-01 14:52:50', 1),
(32, 'Grp.', 'Kategorie II', '22.00', 'EUR', 5, 0, 2, '2015-05-01 14:52:50', 1),
(33, 'Norm.', 'Kategorie III', '20.00', 'EUR', 6, 0, 2, '2015-05-01 14:55:48', 1),
(34, 'Erm.', 'Kategorie III', '15.00', 'EUR', 6, 0, 2, '2015-05-01 14:55:48', 1),
(35, 'Grp.', 'Kategorie III', '14.00', 'EUR', 6, 0, 2, '2015-05-01 14:55:48', 1);

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_tickets`
--

CREATE TABLE `btms_tickets` (
  `id` int(40) NOT NULL,
  `tid` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `event_id` int(40) NOT NULL,
  `date` date DEFAULT NULL,
  `time` time DEFAULT NULL,
  `item_id` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `cat_id` int(40) NOT NULL,
  `art` int(1) NOT NULL,
  `amount` text COLLATE latin1_german1_ci NOT NULL,
  `seats` text COLLATE latin1_german1_ci NOT NULL,
  `status` int(40) NOT NULL,
  `user` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `log` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_tickets`
--

INSERT INTO `btms_tickets` (`id`, `tid`, `event_id`, `date`, `time`, `item_id`, `cat_id`, `art`, `amount`, `seats`, `status`, `user`, `log`) VALUES
(1, '220150915160011483', 2, '2015-09-15', '16:00:00', '37', 4, 1, '37', '1', 0, '1', '2015-10-24 12:34:17'),
(2, '220150915160011483', 2, '2015-09-15', '16:00:00', '37', 4, 1, '37', '2', 4, '1', '2015-10-24 12:34:18'),
(3, '220150915160011483', 2, '2015-09-15', '16:00:00', '37', 4, 1, '37', '3', 0, '1', '2015-10-24 12:34:18'),
(4, '220150915160011491', 2, '2015-09-15', '16:00:00', '35', 4, 1, '35', '1', 0, '1', '2015-10-24 14:59:34'),
(5, '220150915160011491', 2, '2015-09-15', '16:00:00', '35', 4, 1, '35', '2', 2, '1', '2015-10-24 14:59:34');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_transactions`
--

CREATE TABLE `btms_transactions` (
  `id` int(40) NOT NULL,
  `tid` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `event_id` int(40) NOT NULL,
  `date` date DEFAULT NULL,
  `time` time DEFAULT NULL,
  `item_id` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `cat_id` int(40) NOT NULL,
  `art` int(1) NOT NULL,
  `amount` text COLLATE latin1_german1_ci NOT NULL,
  `seats` text COLLATE latin1_german1_ci NOT NULL,
  `status` int(40) NOT NULL,
  `user` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `log` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_transactions`
--

INSERT INTO `btms_transactions` (`id`, `tid`, `event_id`, `date`, `time`, `item_id`, `cat_id`, `art`, `amount`, `seats`, `status`, `user`, `log`) VALUES
(63, '220150915160011418', 2, '2015-09-15', '16:00:00', '41', 6, 2, '{"33";50}', '{}', 3, '1', '2015-10-24 01:12:31'),
(64, '220150915160011426', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";20}', '{}', 3, '1', '2015-10-24 01:14:03'),
(61, '220150915160011400', 2, '2015-09-15', '16:00:00', '26', 4, 1, '{"23";4}', '{"26";{"1";1,"2";1,"3";1,"4";1}}', 1, '1', '2015-10-24 01:08:44'),
(62, '220150915160011418', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";10}', '{}', 3, '1', '2015-10-24 01:12:26'),
(48, '220150915160011350', 2, '2015-09-15', '16:00:00', '23', 4, 1, '{"23";8}', '{"23";{"1";2,"2";2,"3";2,"4";2,"6";2,"7";2,"9";2,"10";2}}', 2, '1', '2015-10-24 00:56:50'),
(49, '220150915160011350', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";1}', '{}', 2, '1', '2015-10-24 00:57:08'),
(50, '220150915160011368', 2, '2015-09-15', '16:00:00', '23', 4, 1, '{"23";4}', '{"23";{"5";1,"8";1,"11";1,"12";1}}', 1, '1', '2015-10-24 00:57:57'),
(51, '220150915160011376', 2, '2015-09-15', '16:00:00', '24', 4, 1, '{"24";3,"25";3,"29";2}', '{"24";{"1";2,"2";2,"3";2,"4";2,"5";2,"6";2,"7";2,"8";2}}', 2, '1', '2015-10-24 00:58:30'),
(52, '220150915160011376', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";1}', '{}', 2, '1', '2015-10-24 00:59:38'),
(53, '220150915160011376', 2, '2015-09-15', '16:00:00', '41', 6, 2, '{"33";1}', '{}', 2, '1', '2015-10-24 00:59:42'),
(54, '220150915160011376', 2, '2015-09-15', '16:00:00', '2', 0, 3, '{"20";1}', '{}', 2, '1', '2015-10-24 01:00:37'),
(55, '220150915160011384', 2, '2015-09-15', '16:00:00', '25', 4, 1, '{"29";1}', '{"25";{"1";2}}', 2, '1', '2015-10-24 01:02:11'),
(56, '220150915160011392', 2, '2015-09-15', '16:00:00', '41', 6, 2, '{"34";1}', '{}', 2, '1', '2015-10-24 01:05:34'),
(57, '220150915160011392', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"32";1}', '{}', 2, '1', '2015-10-24 01:05:34'),
(58, '220150915160011400', 2, '2015-09-15', '16:00:00', '2', 0, 3, '{"20";10}', '{}', 1, '1', '2015-10-24 01:07:17'),
(59, '220150915160011400', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";1}', '{}', 1, '1', '2015-10-24 01:08:04'),
(60, '220150915160011400', 2, '2015-09-15', '16:00:00', '41', 6, 2, '{"33";1}', '{}', 1, '1', '2015-10-24 01:08:07'),
(65, '220150915160011434', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";100}', '{}', 3, '1', '2015-10-24 01:16:08'),
(66, '220150915160011442', 2, '2015-09-15', '16:00:00', '40', 5, 2, '{"30";1050}', '{}', 3, '1', '2015-10-24 01:18:47'),
(67, '220150915160011442', 2, '2015-09-15', '16:00:00', '41', 6, 2, '{"33";80}', '{}', 3, '1', '2015-10-24 01:19:00'),
(68, '220150915160011459', 2, '2015-09-15', '16:00:00', '30', 4, 1, '{"23";4}', '{"30";{"1";2,"2";2,"3";2,"4";2}}', 2, '1', '2015-10-24 12:27:18'),
(69, '220150915160011467', 2, '2015-09-15', '16:00:00', '34', 4, 1, '{"23";3}', '{"34";{"1";2,"2";2,"3";2}}', 2, '1', '2015-10-24 12:27:48'),
(70, '220150915160011475', 2, '2015-09-15', '16:00:00', '38', 4, 1, '{"23";3}', '{"38";{"1";2,"2";2,"3";2}}', 2, '1', '2015-10-24 12:29:17'),
(71, '220150915160011483', 2, '2015-09-15', '16:00:00', '37', 4, 1, '{"23";3}', '{"37";{"1";2,"2";2,"3";2}}', 2, '1', '2015-10-24 12:34:15'),
(72, '220150915160011491', 2, '2015-09-15', '16:00:00', '35', 4, 1, '{"23";2}', '{"35";{"1";2,"2";2}}', 2, '1', '2015-10-24 14:59:31');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_users`
--

CREATE TABLE `btms_users` (
  `id` int(40) NOT NULL,
  `user` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `secret` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `role` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `first_name` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `second_name` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `email` text COLLATE latin1_german1_ci NOT NULL,
  `mobile` varchar(40) COLLATE latin1_german1_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_users`
--

INSERT INTO `btms_users` (`id`, `user`, `secret`, `role`, `first_name`, `second_name`, `email`, `mobile`) VALUES
(1, 'test', 'ae6e334f62fb5d989398deed87568c94', 'frontend', 'Test', 'User', 'test@user.de', '017623108507');

-- --------------------------------------------------------

--
-- Tabellenstruktur für Tabelle `btms_venues`
--

CREATE TABLE `btms_venues` (
  `id` int(30) NOT NULL,
  `ref` int(30) NOT NULL,
  `title` varchar(40) COLLATE latin1_german1_ci NOT NULL,
  `description` text COLLATE latin1_german1_ci NOT NULL,
  `art` int(40) NOT NULL,
  `col` int(40) NOT NULL,
  `row` int(40) NOT NULL,
  `seats` int(40) NOT NULL,
  `size` int(40) NOT NULL,
  `space` text COLLATE latin1_german1_ci NOT NULL,
  `cat_id` int(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_german1_ci;

--
-- Daten für Tabelle `btms_venues`
--

INSERT INTO `btms_venues` (`id`, `ref`, `title`, `description`, `art`, `col`, `row`, `seats`, `size`, `space`, `cat_id`) VALUES
(1, 0, 'Zirkus des Horrors', 'eine Loge weniger wegen Rampe', 0, 0, 0, 0, 0, '', 0),
(2, 1, 'Gruft 1', '', 1, 4, 3, 12, 1, '', 1),
(3, 1, 'Gruft 2', '', 1, 4, 3, 12, 1, '', 1),
(4, 1, 'Gruft 3', '', 1, 4, 3, 12, 0, '', 1),
(5, 1, 'Gruft 4', '', 1, 4, 3, 12, 0, '', 1),
(6, 1, 'Gruft 5', '', 1, 4, 3, 12, 0, '', 1),
(7, 1, 'Gruft 6', '', 1, 4, 3, 12, 0, '', 1),
(8, 1, 'Gruft 7', '', 1, 4, 3, 12, 0, '', 1),
(9, 1, 'Gruft 8', '', 1, 4, 3, 12, 0, '', 1),
(10, 1, 'Gruft 9', '', 1, 4, 3, 12, 0, '', 1),
(11, 1, 'Gruft 10', '', 1, 4, 3, 12, 0, '', 1),
(12, 1, 'Gruft 11', '', 1, 4, 3, 12, 0, '', 1),
(13, 1, 'Gruft 12', '', 1, 4, 3, 12, 0, '', 1),
(14, 1, 'Gruft 13', '', 1, 4, 3, 12, 0, '', 1),
(15, 1, 'Gruft 14', '', 1, 4, 3, 12, 0, '', 1),
(16, 1, 'Gruft 15', '', 1, 4, 3, 12, 0, '', 1),
(17, 1, 'Gruft 16', '', 1, 4, 3, 12, 0, '', 1),
(18, 1, 'Kat II', '', 2, 0, 0, 1131, 0, '', 2),
(19, 1, 'Kat III', '', 2, 0, 0, 100, 0, '', 3),
(20, 0, 'WHZ Karlsruhe', 'ohne Rampe mit einer Loge mehr', 0, 0, 0, 0, 0, '', 0),
(23, 20, 'Loge 1', '', 1, 4, 3, 12, 1, '', 4),
(24, 20, 'Loge 2', '', 1, 4, 3, 12, 1, '', 4),
(25, 20, 'Loge 3', '', 1, 4, 3, 12, 0, '', 4),
(26, 20, 'Loge 4', '', 1, 4, 3, 12, 0, '', 4),
(27, 20, 'Loge 5', '', 1, 4, 3, 12, 0, '', 4),
(28, 20, 'Loge 6', '', 1, 4, 3, 12, 0, '', 4),
(29, 20, 'Loge 7', '', 1, 4, 3, 12, 0, '', 4),
(30, 20, 'Loge 8', '', 1, 4, 3, 12, 0, '', 4),
(31, 20, 'Loge 9', '', 1, 4, 3, 12, 0, '', 4),
(32, 20, 'Loge 10', '', 1, 4, 3, 12, 0, '', 4),
(33, 20, 'Loge 11', '', 1, 4, 3, 12, 0, '', 4),
(34, 20, 'Loge 12', '', 1, 4, 3, 12, 0, '', 4),
(35, 20, 'Loge 13', '', 1, 4, 3, 12, 0, '', 4),
(36, 20, 'Loge 14', '', 1, 4, 3, 12, 0, '', 4),
(37, 20, 'Loge 15', '', 1, 4, 3, 12, 0, '', 4),
(38, 20, 'Loge 16', '', 1, 4, 3, 12, 0, '', 4),
(39, 20, 'Loge 17', '', 1, 4, 3, 12, 0, '', 4),
(40, 20, 'Kat II', '', 2, 0, 0, 1131, 0, '', 5),
(41, 20, 'Kat III', '', 2, 0, 0, 100, 0, '', 6);

--
-- Indizes der exportierten Tabellen
--

--
-- Indizes für die Tabelle `btms_categories`
--
ALTER TABLE `btms_categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_counter`
--
ALTER TABLE `btms_counter`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `btms_events`
--
ALTER TABLE `btms_events`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id_2` (`id`),
  ADD KEY `id` (`id`),
  ADD KEY `id_3` (`id`),
  ADD KEY `id_4` (`id`);

--
-- Indizes für die Tabelle `btms_items`
--
ALTER TABLE `btms_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_journal`
--
ALTER TABLE `btms_journal`
  ADD PRIMARY KEY (`id`);

--
-- Indizes für die Tabelle `btms_prices`
--
ALTER TABLE `btms_prices`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_tickets`
--
ALTER TABLE `btms_tickets`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_transactions`
--
ALTER TABLE `btms_transactions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_users`
--
ALTER TABLE `btms_users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- Indizes für die Tabelle `btms_venues`
--
ALTER TABLE `btms_venues`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- AUTO_INCREMENT für exportierte Tabellen
--

--
-- AUTO_INCREMENT für Tabelle `btms_categories`
--
ALTER TABLE `btms_categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;
--
-- AUTO_INCREMENT für Tabelle `btms_counter`
--
ALTER TABLE `btms_counter`
  MODIFY `id` int(30) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;
--
-- AUTO_INCREMENT für Tabelle `btms_events`
--
ALTER TABLE `btms_events`
  MODIFY `id` int(30) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;
--
-- AUTO_INCREMENT für Tabelle `btms_items`
--
ALTER TABLE `btms_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;
--
-- AUTO_INCREMENT für Tabelle `btms_journal`
--
ALTER TABLE `btms_journal`
  MODIFY `id` int(40) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=105;
--
-- AUTO_INCREMENT für Tabelle `btms_prices`
--
ALTER TABLE `btms_prices`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=36;
--
-- AUTO_INCREMENT für Tabelle `btms_tickets`
--
ALTER TABLE `btms_tickets`
  MODIFY `id` int(40) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
--
-- AUTO_INCREMENT für Tabelle `btms_transactions`
--
ALTER TABLE `btms_transactions`
  MODIFY `id` int(40) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=73;
--
-- AUTO_INCREMENT für Tabelle `btms_users`
--
ALTER TABLE `btms_users`
  MODIFY `id` int(40) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;
--
-- AUTO_INCREMENT für Tabelle `btms_venues`
--
ALTER TABLE `btms_venues`
  MODIFY `id` int(30) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=42;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
