--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

-- Started on 2026-04-14 16:00:00

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 227 (class 1259 OID 29084)
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 37456)
-- Name: backup_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_log (
    id integer NOT NULL,
    filename character varying(255) NOT NULL,
    file_size bigint,
    file_path character varying(512) NOT NULL,
    backup_type character varying(20),
    status character varying(20),
    operation character varying(20),
    error_message text,
    created_at timestamp without time zone,
    created_by_id integer
);


ALTER TABLE public.backup_log OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 37455)
-- Name: backup_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.backup_log_id_seq OWNER TO postgres;

--
-- TOC entry 4931 (class 0 OID 0)
-- Dependencies: 230
-- Name: backup_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_log_id_seq OWNED BY public.backup_log.id;


--
-- TOC entry 229 (class 1259 OID 37444)
-- Name: backup_schedule; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.backup_schedule (
    id integer NOT NULL,
    enabled boolean,
    days_of_week character varying(50),
    execution_time character varying(8),
    backup_format character varying(20),
    retention_days integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    created_by_id integer
);


ALTER TABLE public.backup_schedule OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 37443)
-- Name: backup_schedule_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.backup_schedule_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.backup_schedule_id_seq OWNER TO postgres;

--
-- TOC entry 4932 (class 0 OID 0)
-- Dependencies: 228
-- Name: backup_schedule_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.backup_schedule_id_seq OWNED BY public.backup_schedule.id;


--
-- TOC entry 226 (class 1259 OID 29067)
-- Name: detail_cetak; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.detail_cetak (
    id integer NOT NULL,
    nik character varying(16) NOT NULL,
    nama_lengkap character varying(100) NOT NULL,
    tanggal_cetak timestamp without time zone,
    status_ambil boolean,
    tanggal_ambil timestamp without time zone,
    penerima character varying(100),
    user_id integer NOT NULL,
    kecamatan_id integer NOT NULL,
    hubungan character varying(50),
    status_cetak character varying(20),
    keterangan_gagal character varying(255),
    jenis_cetak character varying(50),
    registrasi_ikd boolean
);


ALTER TABLE public.detail_cetak OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 29066)
-- Name: detail_cetak_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.detail_cetak_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.detail_cetak_id_seq OWNER TO postgres;

--
-- TOC entry 4933 (class 0 OID 0)
-- Dependencies: 225
-- Name: detail_cetak_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.detail_cetak_id_seq OWNED BY public.detail_cetak.id;


--
-- TOC entry 218 (class 1259 OID 29013)
-- Name: kecamatan; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.kecamatan (
    id integer NOT NULL,
    nama_kecamatan character varying(100) NOT NULL,
    kode_wilayah character varying(20) NOT NULL,
    latitude double precision,
    longitude double precision
);


ALTER TABLE public.kecamatan OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 29012)
-- Name: kecamatan_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.kecamatan_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.kecamatan_id_seq OWNER TO postgres;

--
-- TOC entry 4934 (class 0 OID 0)
-- Dependencies: 217
-- Name: kecamatan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.kecamatan_id_seq OWNED BY public.kecamatan.id;


--
-- TOC entry 222 (class 1259 OID 29036)
-- Name: stok; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.stok (
    id integer NOT NULL,
    kecamatan_id integer NOT NULL,
    jumlah_ktp integer,
    jumlah_kia integer,
    last_updated timestamp without time zone
);


ALTER TABLE public.stok OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 29035)
-- Name: stok_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.stok_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.stok_id_seq OWNER TO postgres;

--
-- TOC entry 4935 (class 0 OID 0)
-- Dependencies: 221
-- Name: stok_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.stok_id_seq OWNED BY public.stok.id;


--
-- TOC entry 224 (class 1259 OID 29050)
-- Name: transaksi; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transaksi (
    id integer NOT NULL,
    kecamatan_id integer NOT NULL,
    user_id integer NOT NULL,
    jenis_transaksi character varying(20) NOT NULL,
    jumlah_ktp integer,
    jumlah_kia integer,
    created_at timestamp without time zone,
    keterangan character varying(255)
);


ALTER TABLE public.transaksi OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 29049)
-- Name: transaksi_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transaksi_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transaksi_id_seq OWNER TO postgres;

--
-- TOC entry 4936 (class 0 OID 0)
-- Dependencies: 223
-- Name: transaksi_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transaksi_id_seq OWNED BY public.transaksi.id;


--
-- TOC entry 220 (class 1259 OID 29022)
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(128) NOT NULL,
    role character varying(20) NOT NULL,
    kecamatan_id integer,
    last_login timestamp without time zone,
    nama_lengkap character varying(100),
    created_at timestamp without time zone
);


ALTER TABLE public."user" OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 29021)
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_id_seq OWNER TO postgres;

--
-- TOC entry 4937 (class 0 OID 0)
-- Dependencies: 219
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- TOC entry 4735 (class 2604 OID 37459)
-- Name: backup_log id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_log ALTER COLUMN id SET DEFAULT nextval('public.backup_log_id_seq'::regclass);


--
-- TOC entry 4734 (class 2604 OID 37447)
-- Name: backup_schedule id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_schedule ALTER COLUMN id SET DEFAULT nextval('public.backup_schedule_id_seq'::regclass);


--
-- TOC entry 4733 (class 2604 OID 29070)
-- Name: detail_cetak id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detail_cetak ALTER COLUMN id SET DEFAULT nextval('public.detail_cetak_id_seq'::regclass);


--
-- TOC entry 4729 (class 2604 OID 29016)
-- Name: kecamatan id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kecamatan ALTER COLUMN id SET DEFAULT nextval('public.kecamatan_id_seq'::regclass);


--
-- TOC entry 4731 (class 2604 OID 29039)
-- Name: stok id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stok ALTER COLUMN id SET DEFAULT nextval('public.stok_id_seq'::regclass);


--
-- TOC entry 4732 (class 2604 OID 29053)
-- Name: transaksi id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaksi ALTER COLUMN id SET DEFAULT nextval('public.transaksi_id_seq'::regclass);


--
-- TOC entry 4730 (class 2604 OID 29025)
-- Name: user id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- TOC entry 4921 (class 0 OID 29084)
-- Dependencies: 227
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
f6e9f25b26bc
\.


--
-- TOC entry 4925 (class 0 OID 37456)
-- Dependencies: 231
-- Data for Name: backup_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.backup_log (id, filename, file_size, file_path, backup_type, status, operation, error_message, created_at, created_by_id) FROM stdin;
1	backup_domba_20260414_113200.sql	32300	backups\\backup_domba_20260414_113200.sql	sql	VERIFIED	BACKUP	\N	2026-04-14 11:32:00.651312	\N
\.


--
-- TOC entry 4923 (class 0 OID 37444)
-- Dependencies: 229
-- Data for Name: backup_schedule; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.backup_schedule (id, enabled, days_of_week, execution_time, backup_format, retention_days, created_at, updated_at, created_by_id) FROM stdin;
1	t	[0, 1, 2, 3, 4, 5, 6]	16:00	sql	30	2026-04-14 11:08:02.811359	2026-04-14 11:34:38.045836	\N
\.


--
-- TOC entry 4920 (class 0 OID 29067)
-- Dependencies: 226
-- Data for Name: detail_cetak; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.detail_cetak (id, nik, nama_lengkap, tanggal_cetak, status_ambil, tanggal_ambil, penerima, user_id, kecamatan_id, hubungan, status_cetak, keterangan_gagal, jenis_cetak, registrasi_ikd) FROM stdin;
1	3276052404990001	RIZKI ADE MAULANA	2026-01-07 13:30:30.186989	t	2026-01-07 20:47:51.901789	RIZKI ADE MAULANA	26	26	Yang Bersangkutan	\N	\N	\N	\N
2	3205240499000222	YAYAT	2026-01-08 02:06:19.05347	t	2026-01-08 09:07:04.089377	YIYIT	26	26	Istri	\N	\N	\N	\N
3	1231231231231231	BAMBANG	2026-01-08 04:39:40.765248	t	2026-01-08 11:40:23.392926	YATI	27	27	Istri	BERHASIL	\N	\N	\N
6	3205010101010100	LELES	2026-02-04 09:00:06.353443	t	2026-02-04 09:04:04.903432	LELES	26	26	Yang Bersangkutan	BERHASIL	\N	Cetak Baru	f
8	3276052404040404	TEST	2026-04-02 15:30:24.013203	f	\N	\N	1	1	\N	BERHASIL	\N	Cetak Baru	f
9	1234512345123451	SATUDUATIGA	2026-04-14 12:18:57.445462	f	\N	\N	1	1	\N	BERHASIL	\N	Cetak Baru	t
\.


--
-- TOC entry 4912 (class 0 OID 29013)
-- Dependencies: 218
-- Data for Name: kecamatan; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.kecamatan (id, nama_kecamatan, kode_wilayah, latitude, longitude) FROM stdin;
2	Kecamatan Garut Kota	32.05.01	\N	\N
3	Kecamatan Tarogong Kidul	32.05.02	\N	\N
44	Kecamatan Wanaraja	32.05.42	\N	\N
5	Kecamatan Banjarwangi	32.05.03	\N	\N
6	Kecamatan Banyuresmi	32.05.04	\N	\N
7	Kecamatan Bayongbong	32.05.05	\N	\N
8	Kecamatan Blubur Limbangan	32.05.06	\N	\N
9	Kecamatan Bungbulang	32.05.07	\N	\N
10	Kecamatan Caringin	32.05.08	\N	\N
11	Kecamatan Cibalong	32.05.09	\N	\N
12	Kecamatan Cibatu	32.05.10	\N	\N
13	Kecamatan Cibiuk	32.05.11	\N	\N
14	Kecamatan Cigedug	32.05.12	\N	\N
15	Kecamatan Cihurip	32.05.13	\N	\N
16	Kecamatan Cikajang	32.05.14	\N	\N
17	Kecamatan Cikelet	32.05.15	\N	\N
18	Kecamatan Cilawu	32.05.16	\N	\N
19	Kecamatan Cisewu	32.05.17	\N	\N
20	Kecamatan Cisompet	32.05.18	\N	\N
21	Kecamatan Cisurupan	32.05.19	\N	\N
22	Kecamatan Kadungora	32.05.20	\N	\N
23	Kecamatan Karangpawitan	32.05.21	\N	\N
24	Kecamatan Karangtengah	32.05.22	\N	\N
25	Kecamatan Kersamanah	32.05.23	\N	\N
26	Kecamatan Leles	32.05.24	\N	\N
27	Kecamatan Leuwigoong	32.05.25	\N	\N
28	Kecamatan Malangbong	32.05.26	\N	\N
29	Kecamatan Mekarmukti	32.05.27	\N	\N
30	Kecamatan Pakenjeng	32.05.28	\N	\N
31	Kecamatan Pameungpeuk	32.05.29	\N	\N
32	Kecamatan Pamulihan	32.05.30	\N	\N
33	Kecamatan Pangatikan	32.05.31	\N	\N
34	Kecamatan Pasirwangi	32.05.32	\N	\N
35	Kecamatan Peundeuy	32.05.33	\N	\N
36	Kecamatan Samarang	32.05.34	\N	\N
37	Kecamatan Selaawi	32.05.35	\N	\N
38	Kecamatan Singajaya	32.05.36	\N	\N
39	Kecamatan Sucinaraja	32.05.37	\N	\N
40	Kecamatan Sukaresmi	32.05.38	\N	\N
41	Kecamatan Sukawening	32.05.39	\N	\N
42	Kecamatan Talegong	32.05.40	\N	\N
43	Kecamatan Tarogong Kaler	32.05.41	\N	\N
1	Dinas	32.05.00	\N	\N
\.


--
-- TOC entry 4916 (class 0 OID 29036)
-- Dependencies: 222
-- Data for Name: stok; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.stok (id, kecamatan_id, jumlah_ktp, jumlah_kia, last_updated) FROM stdin;
2	2	0	0	2026-01-07 09:01:09.881429
4	5	0	0	2026-01-07 09:10:12.341145
5	6	0	0	2026-01-07 09:10:12.342633
6	7	0	0	2026-01-07 09:10:12.343415
7	8	0	0	2026-01-07 09:10:12.344134
9	10	0	0	2026-01-07 09:10:12.345569
10	11	0	0	2026-01-07 09:10:12.346353
11	12	0	0	2026-01-07 09:10:12.347094
12	13	0	0	2026-01-07 09:10:12.347798
13	14	0	0	2026-01-07 09:10:12.348497
14	15	0	0	2026-01-07 09:10:12.349174
15	16	0	0	2026-01-07 09:10:12.349846
16	17	0	0	2026-01-07 09:10:12.350544
17	18	0	0	2026-01-07 09:10:12.351236
18	19	0	0	2026-01-07 09:10:12.351913
19	20	0	0	2026-01-07 09:10:12.352599
20	21	0	0	2026-01-07 09:10:12.353271
21	22	0	0	2026-01-07 09:10:12.353938
22	23	0	0	2026-01-07 09:10:12.354624
23	24	0	0	2026-01-07 09:10:12.355459
24	25	0	0	2026-01-07 09:10:12.356337
27	28	0	0	2026-01-07 09:10:12.358438
28	29	0	0	2026-01-07 09:10:12.359132
29	30	0	0	2026-01-07 09:10:12.3598
30	31	0	0	2026-01-07 09:10:12.360507
31	32	0	0	2026-01-07 09:10:12.361166
32	33	0	0	2026-01-07 09:10:12.361859
33	34	0	0	2026-01-07 09:10:12.362558
34	35	0	0	2026-01-07 09:10:12.363471
35	36	0	0	2026-01-07 09:10:12.364165
36	37	0	0	2026-01-07 09:10:12.364852
37	38	0	0	2026-01-07 09:10:12.365518
38	39	0	0	2026-01-07 09:10:12.366174
39	40	0	0	2026-01-07 09:10:12.366855
40	41	0	0	2026-01-07 09:10:12.367551
41	42	0	0	2026-01-07 09:10:12.368268
42	43	0	0	2026-01-07 09:10:12.368862
43	44	0	0	2026-01-07 09:14:34.68574
3	3	0	0	2026-01-07 13:20:00.96295
26	27	1	0	2026-02-04 09:38:36.988152
25	26	197	0	2026-02-04 09:40:26.344323
8	9	100	0	2026-04-02 15:32:13.614475
1	1	1848	0	2026-04-14 12:18:57.451121
\.


--
-- TOC entry 4918 (class 0 OID 29050)
-- Dependencies: 224
-- Data for Name: transaksi; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transaksi (id, kecamatan_id, user_id, jenis_transaksi, jumlah_ktp, jumlah_kia, created_at, keterangan) FROM stdin;
1	1	1	IN_FROM_PUSAT	10000	0	2026-01-07 09:01:27	\N
2	26	1	DISTRIBUSI_TO_KEC	100	0	2026-01-07 09:03:58.595802	\N
3	26	26	CETAK	1	0	2026-01-07 13:30:30.190765	\N
4	1	2	IN_FROM_PUSAT	1000	0	2026-01-08 02:04:59.117611	\N
5	26	2	DISTRIBUSI_TO_KEC	50	0	2026-01-08 02:05:23.374307	\N
6	26	26	CETAK	1	0	2026-01-08 02:06:19.0615	\N
7	1	2	IN_FROM_PUSAT	1000	0	2026-01-08 04:36:57	\N
8	27	2	DISTRIBUSI_TO_KEC	100	0	2026-01-08 04:38:08.21141	\N
9	27	27	CETAK	1	0	2026-01-08 04:39:40.76714	\N
10	27	27	CETAK	1	0	2026-01-08 04:49:46.711226	\N
11	27	27	CETAK	1	0	2026-01-08 07:48:01.347321	\N
12	27	27	PENGEMBALIAN	1	0	2026-01-08 07:48:31.899633	\N
13	1	1	IN_FROM_PUSAT	10	0	2026-01-08 15:01:53.351401	\N
14	1	1	STOCK_ADJUSTMENT	-10760	0	2026-01-08 15:37:01.083521	\N
15	1	1	STOCK_ADJUSTMENT	0	0	2026-01-08 15:37:06.259551	\N
16	27	1	STOCK_ADJUSTMENT	-98	0	2026-01-08 15:46:39.272273	\N
17	27	1	DISTRIBUSI_TO_KEC	0	0	2026-01-08 16:05:26.478605	\N
18	1	1	STOCK_ADJUSTMENT	0	0	2026-01-08 16:05:45.013401	\N
19	26	26	CETAK	1	0	2026-02-04 09:00:06.366486	\N
20	1	1	CETAK	1	0	2026-02-04 09:34:55.812502	\N
21	26	1	DISTRIBUSI_TO_KEC	50	0	2026-02-04 09:40:26.345946	\N
22	1	1	CETAK	1	0	2026-04-02 15:30:24.03084	\N
23	1	1	IN_FROM_PUSAT	1000	0	2026-04-02 15:30:55.243572	april
24	9	1	DISTRIBUSI_TO_KEC	100	0	2026-04-02 15:32:13.614869	\N
25	1	1	CETAK	1	0	2026-04-14 12:18:57.453353	\N
26	42	42	Masuk	5	5	2026-04-14 12:46:35.957408	Sample Transaction for Kecamatan Talegong
27	29	29	Masuk	5	5	2026-04-14 12:46:35.966499	Sample Transaction for Kecamatan Mekarmukti
28	34	34	Masuk	5	5	2026-04-14 12:46:35.968258	Sample Transaction for Kecamatan Pasirwangi
29	41	41	Masuk	5	5	2026-04-14 12:46:35.969436	Sample Transaction for Kecamatan Sukawening
30	40	40	Masuk	5	5	2026-04-14 12:46:35.970503	Sample Transaction for Kecamatan Sukaresmi
\.


--
-- TOC entry 4914 (class 0 OID 29022)
-- Dependencies: 220
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."user" (id, username, password_hash, role, kecamatan_id, last_login, nama_lengkap, created_at) FROM stdin;
24	3205karangtengah	pbkdf2:sha256:600000$e0hSLEoRNGq4DGKY$7392dd8fba897d29f238b4872dede7d3affe49719f9996b2937eff22aa967a8d	operator_kecamatan	24	\N	Kecamatan Karangtengah	\N
47	3205refqi	pbkdf2:sha256:600000$xZJC48gnDKUWNFDA$a2f402638abb1405c14669a7e8c7ec0a2f43ee917fb036b95b5f3648eb9c76a4	admin_dinas	1	\N	Refqi	2026-02-11 13:12:16.606352
45	3205sabtian	pbkdf2:sha256:600000$MpjIZy5dU53JKUF4$60f940c8b90e50bf9bf2f25843039b08e8599a32bbcfe85b8edb4da4cd020331	admin_dinas	1	\N	Sabtian	2026-01-23 10:29:11.389126
2	3205dery	pbkdf2:sha256:600000$FK5rER3jUbvRAJnx$0c0ab1c2759ce4cf6e66dbdca5d5964b1421c5fa96bcb57c064d4627cf0d4238	admin_dinas	1	2026-01-08 04:34:41.103799	Dery Fristama	\N
46	3205fery	pbkdf2:sha256:600000$aiiBK7aLJmA17qGn$839713ad9e0277fd13250e3dac0336984c096c4d336ef63fb3a872d58494c875	admin_dinas	\N	\N	Fery	2026-01-27 09:21:54.963577
4	3205tarogongkidul	pbkdf2:sha256:600000$QXHSRvb3TBa5pIVS$fc5cb0514e53aeb612d908b6c03a9775d9638e215512cad2ff16e774cff2aaf4	operator_kecamatan	3	\N	Kecamatan Tarogong Kidul	\N
1	administrator	pbkdf2:sha256:600000$ayr165euzVhrhlha$e796ddd5d02a38d4c0253563d667f3fa4f08e145f14d067c5ae3ad1747528435	admin_dinas	1	2026-04-14 14:33:16.095057	RIZKI ADE MAULANA	\N
44	3205hening	pbkdf2:sha256:600000$0pJbvu5ROaFg0Vv8$da47979eb0a6a2a6149b410c76ff45a8ab475aeb18fba99d560c1c6da6513c6c	admin_dinas	\N	\N	Hening Nur Azizah	2026-01-09 09:14:57.406939
27	3205leuwigoong	pbkdf2:sha256:600000$XFvkhTlTJ2EICWZC$d78f473076a26606e5969ebaa73a34704ff49f0110c87aeb28fe21c35ef7f02d	operator_kecamatan	27	2026-01-09 16:00:16.604138	Kecamatan Leuwigoong	\N
3	3205garutkota	pbkdf2:sha256:600000$JCrNgnRWDUf2ulZB$7f6dc63d2d37e35f676115138f85a890fbd9b4fa0f281883f94fc8e90975c3c7	operator_kecamatan	2	\N	Kecamatan Garut Kota	\N
5	3205banjarwangi	pbkdf2:sha256:600000$FsBbwJ0VnsVO7Udk$fbe0328329e5da49c52e696a677c922fde5b7ba89963be133338ae688f290480	operator_kecamatan	5	\N	Kecamatan Banjarwangi	\N
22	3205kadungora	pbkdf2:sha256:600000$PHyISyTaVyh9aucY$88f432f963c067560fa50df2adf6394dea69e332867707afff490cd247519b17	operator_kecamatan	22	\N	Kecamatan Kadungora	\N
23	3205karangpawitan	pbkdf2:sha256:600000$187ksCCOJ2rjQkDv$cedc2f398a5f35bd19bceb8595c4118cea743e135a2b1fdd30d9d8cddddcb06f	operator_kecamatan	23	\N	Kecamatan Karangpawitan	\N
25	3205kersamanah	pbkdf2:sha256:600000$Mfd03i36X97i1ZmY$d13917765a82002add229052d267597e01b5b389bf522ca51ba416f6da75d98a	operator_kecamatan	25	\N	Kecamatan Kersamanah	\N
28	3205malangbong	pbkdf2:sha256:600000$RHuUz1OkcrbIwMJk$399d926aa9316e782a81b7aa402650a5299de84b5a1e1c6a2e56a2362f5d4049	operator_kecamatan	28	\N	Kecamatan Malangbong	\N
29	3205mekarmukti	pbkdf2:sha256:600000$77rOIy7jROGVHUeY$0977ec136eaea45cd60b4063c46149e9a876a6750a51296d86f156c268e7cb6b	operator_kecamatan	29	\N	Kecamatan Mekarmukti	\N
30	3205pakenjeng	pbkdf2:sha256:600000$coeU8r71yjjjdDuj$b3e392f5e0c516ac6d1a8bf4607539ed829002c076c3e723156af6c942823aa9	operator_kecamatan	30	\N	Kecamatan Pakenjeng	\N
31	3205pameungpeuk	pbkdf2:sha256:600000$IRYmVQQB9Y6eSX90$95aa2ef9b92f83d33977fdc3963d9ecc53aaf12baea21925c7cb941574f193a3	operator_kecamatan	31	\N	Kecamatan Pameungpeuk	\N
32	3205pamulihan	pbkdf2:sha256:600000$XYIjTxQfPxLReTXo$ac221f24a02ba8fe999d086d4235d79e9a95d2b56d7721ef2e3c8be42745f1bc	operator_kecamatan	32	\N	Kecamatan Pamulihan	\N
33	3205pangatikan	pbkdf2:sha256:600000$FzrWXmRUfEKvh6U5$9cd0aafbef90fe22ee430a41e70023c0e707fcb3a96327b66599ee0e4d49163c	operator_kecamatan	33	\N	Kecamatan Pangatikan	\N
34	3205pasirwangi	pbkdf2:sha256:600000$sk6BWib57J68wd6u$04a57e9e3f2a3fdd09c8a04d7c92d57eea9eac3f8994b3d2ad398bc374c9a4b6	operator_kecamatan	34	\N	Kecamatan Pasirwangi	\N
35	3205peundeuy	pbkdf2:sha256:600000$TsiKMJzmGQcsWbCb$33da05bde3316edb756a426590291d72d486bf442f925d0a8efb0dd5cc0df2dd	operator_kecamatan	35	\N	Kecamatan Peundeuy	\N
36	3205samarang	pbkdf2:sha256:600000$RB7h1i82jQoK7I6s$f073eaed5c2127ccdefbad95a1e1af00bda33e48da9730a2ce8dbe53f9faa7aa	operator_kecamatan	36	\N	Kecamatan Samarang	\N
37	3205selaawi	pbkdf2:sha256:600000$4xProQiKYp9qXQRU$e69e553f59dd773b9e5a49c04e7ced45c244ef9dc817d2ca017ee0f5e6f01d3e	operator_kecamatan	37	\N	Kecamatan Selaawi	\N
38	3205singajaya	pbkdf2:sha256:600000$ErcR398sQGDEL8zN$8595408815153c2b7f1da44234e80bbc67b8588002c05ebbdae2b9a4505d2148	operator_kecamatan	38	\N	Kecamatan Singajaya	\N
39	3205sucinaraja	pbkdf2:sha256:600000$5pTiRPNwD7WqWNDm$8f4d79c9f7e27693febbece783503c7d519ec9e8f2f2de75fac38c9761eebcea	operator_kecamatan	39	\N	Kecamatan Sucinaraja	\N
40	3205sukaresmi	pbkdf2:sha256:600000$oIPbaPtAeoHToirN$940a4a40746856d847ff6112c5b6bb32647c02bea3ee761503c15cb8fa59a542	operator_kecamatan	40	\N	Kecamatan Sukaresmi	\N
41	3205sukawening	pbkdf2:sha256:600000$EWI6wJxlTVBFC7CA$a95ff7c357995330c67f46981b507bc07c4ed2d89d4c78c93924998f84921cbc	operator_kecamatan	41	\N	Kecamatan Sukawening	\N
42	3205talegong	pbkdf2:sha256:600000$oREEvPEtEBw71coS$22a88905fa511aac31409a3aeb68df4ee3503acfe01792aedc441be26f4b9c81	operator_kecamatan	42	\N	Kecamatan Talegong	\N
43	3205tarogongkaler	pbkdf2:sha256:600000$KZ9nvb8biaiDevZ3$db728bb65b7f1d7e7e090ed7cefc2864f4eb1b133a8481879d0c557ba9903bd2	operator_kecamatan	43	\N	Kecamatan Tarogong Kaler	\N
6	3205banyuresmi	pbkdf2:sha256:600000$dancQEAL9uChsBxx$a1ba3cdfdbb224ca12cec60d74e2729136fd0d47c4faa7ee94170b190fa57118	operator_kecamatan	6	\N	Kecamatan Banyuresmi	\N
7	3205bayongbong	pbkdf2:sha256:600000$ArIRlCSn8tYg3JJ3$e8312c951b47678394a868381efa0639df87af2f11ce4df5386ce8ed4867454c	operator_kecamatan	7	\N	Kecamatan Bayongbong	\N
8	3205bluburlimbangan	pbkdf2:sha256:600000$F4wU3JQSX0RZNHCq$d8ecc860d21da5fb27b092dcb62e829ff6e71fed62a0ec000858f2630f4e23d4	operator_kecamatan	8	\N	Kecamatan Blubur Limbangan	\N
9	3205bungbulang	pbkdf2:sha256:600000$y3UnIncNBqy8kM9v$9758719d12ce35d06755d39da90d9f50aa7a61380d2421c82400c7a900ffc7e2	operator_kecamatan	9	\N	Kecamatan Bungbulang	\N
10	3205caringin	pbkdf2:sha256:600000$3YeYBofe3HffgRyx$dc763a22b1a1b16f4b8599f59fcd6ba59ab72cdfe189be5140ebc7317b4b3251	operator_kecamatan	10	\N	Kecamatan Caringin	\N
11	3205cibalong	pbkdf2:sha256:600000$tF9n196KE0CGF02N$06d7c6e31104f678a4cfc833edda664fc6b6eb557a99b9312713c0e9c5db2532	operator_kecamatan	11	\N	Kecamatan Cibalong	\N
12	3205cibatu	pbkdf2:sha256:600000$jNNWXbCIkbvY1tU9$eb8704f358e604ca3533d34a8475d9b0c3362059dd6dd562b9837e021023ad12	operator_kecamatan	12	\N	Kecamatan Cibatu	\N
26	3205leles	pbkdf2:sha256:600000$ezMNhUPA145XMF4i$17187346ac8b99eb0df36fc7e45e9d2fa537d2a509e2e34077104a43447a4fb1	operator_kecamatan	26	2026-02-04 09:12:38.691469	Kecamatan Leles	\N
13	3205cibiuk	pbkdf2:sha256:600000$93WVSnQLPV4q0nQs$90ede50db5f84384d6ef3fb170519fb1c84864c9d0a1949b2352c739a02d025c	operator_kecamatan	13	\N	Kecamatan Cibiuk	\N
14	3205cigedug	pbkdf2:sha256:600000$qRu4yFrSghQCu6VB$fa65ed2e687890bcb65c715c804917eab37193786f62216606cb3b696397f731	operator_kecamatan	14	\N	Kecamatan Cigedug	\N
15	3205cihurip	pbkdf2:sha256:600000$K61qhNbqLMcfRVgd$e54a5d1dfe27a27594ed9dd9fa2a39512cedac2cb0fab418b3cf5b7eaa9b1c84	operator_kecamatan	15	\N	Kecamatan Cihurip	\N
16	3205cikajang	pbkdf2:sha256:600000$yXClGVJeRbjwH9w0$15e29bb10cf5aea6c01eee9ec4650db5c22cee12b9b2c8f9813e16ab8790dff9	operator_kecamatan	16	\N	Kecamatan Cikajang	\N
17	3205cikelet	pbkdf2:sha256:600000$qUh765Q9pGEJE2YK$2d6836550a73870c3be2f49fd300f83cf76afb85567abe340ee5c9b8fac7ea9f	operator_kecamatan	17	\N	Kecamatan Cikelet	\N
18	3205cilawu	pbkdf2:sha256:600000$ibSEQoTHbTmX4JCH$cd8f6cc9b2695b440482ce7f36a479eb4c9b981b6635e53e49873647bd170c18	operator_kecamatan	18	\N	Kecamatan Cilawu	\N
19	3205cisewu	pbkdf2:sha256:600000$v3Km8w47gcWMjbTj$8ddddac666aa5464e3a9dd16df59529fcec09c55d7583b1e0ee7c1a8adfd22b2	operator_kecamatan	19	\N	Kecamatan Cisewu	\N
20	3205cisompet	pbkdf2:sha256:600000$M2uD3lxCb34MJ4sk$a71c844fa8b94b252f6d2df2e59cd9e2852bec3b2c2d85bb033c2f7e65291d0d	operator_kecamatan	20	\N	Kecamatan Cisompet	\N
21	3205cisurupan	pbkdf2:sha256:600000$aK1IPOqEllyFqlQI$84eaaeeb389d8846a7fa14407dda7f15f0cb560aeca95023d598c389787145fe	operator_kecamatan	21	\N	Kecamatan Cisurupan	\N
\.


--
-- TOC entry 4938 (class 0 OID 0)
-- Dependencies: 230
-- Name: backup_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.backup_log_id_seq', 2, true);


--
-- TOC entry 4939 (class 0 OID 0)
-- Dependencies: 228
-- Name: backup_schedule_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.backup_schedule_id_seq', 1, true);


--
-- TOC entry 4940 (class 0 OID 0)
-- Dependencies: 225
-- Name: detail_cetak_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.detail_cetak_id_seq', 9, true);


--
-- TOC entry 4941 (class 0 OID 0)
-- Dependencies: 217
-- Name: kecamatan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.kecamatan_id_seq', 44, true);


--
-- TOC entry 4942 (class 0 OID 0)
-- Dependencies: 221
-- Name: stok_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.stok_id_seq', 43, true);


--
-- TOC entry 4943 (class 0 OID 0)
-- Dependencies: 223
-- Name: transaksi_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transaksi_id_seq', 30, true);


--
-- TOC entry 4944 (class 0 OID 0)
-- Dependencies: 219
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_id_seq', 47, true);


--
-- TOC entry 4753 (class 2606 OID 29088)
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- TOC entry 4757 (class 2606 OID 37463)
-- Name: backup_log backup_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_log
    ADD CONSTRAINT backup_log_pkey PRIMARY KEY (id);


--
-- TOC entry 4755 (class 2606 OID 37449)
-- Name: backup_schedule backup_schedule_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_schedule
    ADD CONSTRAINT backup_schedule_pkey PRIMARY KEY (id);


--
-- TOC entry 4751 (class 2606 OID 29072)
-- Name: detail_cetak detail_cetak_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detail_cetak
    ADD CONSTRAINT detail_cetak_pkey PRIMARY KEY (id);


--
-- TOC entry 4737 (class 2606 OID 29020)
-- Name: kecamatan kecamatan_kode_wilayah_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kecamatan
    ADD CONSTRAINT kecamatan_kode_wilayah_key UNIQUE (kode_wilayah);


--
-- TOC entry 4739 (class 2606 OID 29018)
-- Name: kecamatan kecamatan_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.kecamatan
    ADD CONSTRAINT kecamatan_pkey PRIMARY KEY (id);


--
-- TOC entry 4745 (class 2606 OID 29043)
-- Name: stok stok_kecamatan_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stok
    ADD CONSTRAINT stok_kecamatan_id_key UNIQUE (kecamatan_id);


--
-- TOC entry 4747 (class 2606 OID 29041)
-- Name: stok stok_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stok
    ADD CONSTRAINT stok_pkey PRIMARY KEY (id);


--
-- TOC entry 4749 (class 2606 OID 29055)
-- Name: transaksi transaksi_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaksi
    ADD CONSTRAINT transaksi_pkey PRIMARY KEY (id);


--
-- TOC entry 4741 (class 2606 OID 29027)
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- TOC entry 4743 (class 2606 OID 29029)
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- TOC entry 4765 (class 2606 OID 37464)
-- Name: backup_log backup_log_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_log
    ADD CONSTRAINT backup_log_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);


--
-- TOC entry 4764 (class 2606 OID 37450)
-- Name: backup_schedule backup_schedule_created_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.backup_schedule
    ADD CONSTRAINT backup_schedule_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public."user"(id);


--
-- TOC entry 4762 (class 2606 OID 29078)
-- Name: detail_cetak detail_cetak_kecamatan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detail_cetak
    ADD CONSTRAINT detail_cetak_kecamatan_id_fkey FOREIGN KEY (kecamatan_id) REFERENCES public.kecamatan(id);


--
-- TOC entry 4763 (class 2606 OID 29073)
-- Name: detail_cetak detail_cetak_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.detail_cetak
    ADD CONSTRAINT detail_cetak_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- TOC entry 4759 (class 2606 OID 29044)
-- Name: stok stok_kecamatan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.stok
    ADD CONSTRAINT stok_kecamatan_id_fkey FOREIGN KEY (kecamatan_id) REFERENCES public.kecamatan(id);


--
-- TOC entry 4760 (class 2606 OID 29056)
-- Name: transaksi transaksi_kecamatan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaksi
    ADD CONSTRAINT transaksi_kecamatan_id_fkey FOREIGN KEY (kecamatan_id) REFERENCES public.kecamatan(id);


--
-- TOC entry 4761 (class 2606 OID 29061)
-- Name: transaksi transaksi_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaksi
    ADD CONSTRAINT transaksi_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- TOC entry 4758 (class 2606 OID 29030)
-- Name: user user_kecamatan_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_kecamatan_id_fkey FOREIGN KEY (kecamatan_id) REFERENCES public.kecamatan(id);


-- Completed on 2026-04-14 16:00:00

--
-- PostgreSQL database dump complete
--

