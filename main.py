import pandas as pd
import vizro.plotly.express as px
import vizro.models as vm
from vizro import Vizro
from vizro.tables import dash_ag_grid
import streamlit as st

uploaded_file = st.file_uploader("Upload file CSV")
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    st.write(data.head())

data = pd.read_csv("DATASET_PUSKESMAS_RANDOM_ALOKASI_REALISASI.csv") 

print(data.columns)

df = data.dropna()
jumlah_sebelum = len(data)
print("sebelum dibersihkan:", jumlah_sebelum)
jumlah_setelah = len(df)
print("Setelah dibersihkan:", jumlah_setelah)

kolom_dibutuhkan = [
    "Nama Puskesmas", "Kode Puskesmas", "Karakter Puskesmas", "Provinsi",
    "NAMA KAB/KOTA", "TAHUN", "FS1", "FA1", "HP1", "PR1", "REALISASI BELANJA (RP)", "ALOKASI BELANJA (RP)"
]
df_subset = df[kolom_dibutuhkan]

df_subset.to_csv("realisasi_puskesmas.csv", index=False)

# def format_rupiah_singkat(angka):
#     if angka >= 1_000_000_000_000:
#         return f"Rp {angka / 1_000_000_000_000:.2f} Triliun"
#     elif angka >= 1_000_000_000:
#         return f"Rp {angka / 1_000_000_000:.2f} Miliar"
#     elif angka >= 1_000_000:
#         return f"Rp {angka / 1_000_000:.2f} Juta"
#     elif angka >= 1_000:
#         return f"Rp {angka / 1_000:.2f} Ribu"
#     else:
#         return f"Rp {angka:.0f}"
def format_rupiah_singkat(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# Informasi wilayah #
df_wilayah = df[["Nama Puskesmas", "Kode Puskesmas", "Karakter Puskesmas", "Provinsi", "NAMA KAB/KOTA", "TAHUN"]]\
    .drop_duplicates().dropna().rename(columns={"NAMA KAB/KOTA": "Kabupaten/Kota", "TAHUN": "Tahun", "Karakter Puskesmas": "Karakteristik"})
df_belanja = df.groupby(["Nama Puskesmas", "Kode Puskesmas"], as_index=False)[
    ["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]
].sum()
df_belanja["Sisa Belanja"] = df_belanja["ALOKASI BELANJA (RP)"] - df_belanja["REALISASI BELANJA (RP)"]
df_belanja["Tingkat Realisasi (%)"] = (
    df_belanja["REALISASI BELANJA (RP)"] / df_belanja["ALOKASI BELANJA (RP)"]
) * 100
# 
df_wilayah_belanja = pd.merge(df_wilayah, df_belanja, on=["Nama Puskesmas", "Kode Puskesmas"], how="left")
df_wilayah_belanja["Tingkat Realisasi Angka"] = df_wilayah_belanja["Tingkat Realisasi (%)"]
df_wilayah_belanja["Realisasi Belanja"] = df_wilayah_belanja["REALISASI BELANJA (RP)"].apply(format_rupiah_singkat)
df_wilayah_belanja["Alokasi Belanja"] = df_wilayah_belanja["ALOKASI BELANJA (RP)"].apply(format_rupiah_singkat)
df_wilayah_belanja["Sisa Belanja"] = df_wilayah_belanja["Sisa Belanja"].apply(format_rupiah_singkat)
df_wilayah_belanja["Tingkat Realisasi (%)"] = df_wilayah_belanja["Tingkat Realisasi Angka"].round(2).astype(str) + "%"
#
def kategorikan_efektivitas(persen):
    if persen > 100:
        return "Sangat Efektif (100%)"
    elif persen >= 90:
        return "Efektif (>= 90%)"
    elif persen >= 80:
        return "Cukup Efektif (>= 80%)"
    elif persen >= 60:
        return "Kurang Efektif (>= 60%)"
    else:
        return "Tidak Efektif (< 60%)"
df_wilayah_belanja["Kategori Efektivitas"] = df_wilayah_belanja["Tingkat Realisasi Angka"].apply(kategorikan_efektivitas)
df_kategori_persen = df_wilayah_belanja.groupby(["Tahun", "Kategori Efektivitas"]).size().reset_index(name="Jumlah")
df_karakter_kategori = df_wilayah_belanja.groupby(["Tahun", "Karakteristik", "Kategori Efektivitas"]).size().reset_index(name="Jumlah")
df_provinsi_kategori = df_wilayah_belanja.groupby(["Tahun", "Provinsi", "Kategori Efektivitas"]).size().reset_index(name="Jumlah")
df_kabko_kategori = df_wilayah_belanja.groupby(["Tahun", "Kabupaten/Kota", "Kategori Efektivitas"]).size().reset_index(name="Jumlah")

## Realisasi Belanja Menurut Sumber ##
df_realisasi_belanja_sumber = df.groupby(["FS1", "TAHUN"], as_index=False)[
    ["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]
].sum().rename(columns={"TAHUN": "Tahun", "FS1": "Sumber Pembiayaan"})
df_realisasi_belanja_sumber["Realisasi Belanja"] = df_realisasi_belanja_sumber[
    "REALISASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_sumber["Alokasi Belanja"] = df_realisasi_belanja_sumber[
    "ALOKASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_sumber["Tingkat Realisasi (%)"] = (
    df_realisasi_belanja_sumber["REALISASI BELANJA (RP)"] /
    df_realisasi_belanja_sumber["ALOKASI BELANJA (RP)"] * 100
).round(2)
df_realisasi_belanja_sumber["Tingkat Realisasi (%)"] = df_realisasi_belanja_sumber["Tingkat Realisasi (%)"].astype(str) + "%"

## Realisasi Belanja Menurut Pengelola Anggaran ##
df_realisasi_belanja_pengelola_anggaran = df.groupby(["FA1", "TAHUN"], as_index=False)[
    ["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]
].sum().rename(columns={"TAHUN": "Tahun", "FA1": "Pengelola Anggaran"})
df_realisasi_belanja_pengelola_anggaran["Realisasi Belanja"] = df_realisasi_belanja_pengelola_anggaran[
    "REALISASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_pengelola_anggaran["Alokasi Belanja"] = df_realisasi_belanja_pengelola_anggaran[
    "ALOKASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_pengelola_anggaran["Tingkat Realisasi (%)"] = (
    df_realisasi_belanja_pengelola_anggaran["REALISASI BELANJA (RP)"] /
    df_realisasi_belanja_pengelola_anggaran["ALOKASI BELANJA (RP)"] * 100
).round(2)
df_realisasi_belanja_pengelola_anggaran["Tingkat Realisasi (%)"] = df_realisasi_belanja_pengelola_anggaran["Tingkat Realisasi (%)"].astype(str) + "%"

## Realisasi Belanja Menurut Penyedia Pelayanan ##
df_realisasi_belanja_penyedia_pelayanan = df.groupby(["HP1", "TAHUN"], as_index=False)[
    ["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]
].sum().rename(columns={"TAHUN": "Tahun", "HP1": "Penyedia Pelayanan"})
df_realisasi_belanja_penyedia_pelayanan["Realisasi Belanja"] = df_realisasi_belanja_penyedia_pelayanan[
    "REALISASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_penyedia_pelayanan["Alokasi Belanja"] = df_realisasi_belanja_penyedia_pelayanan[
    "ALOKASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_penyedia_pelayanan["Tingkat Realisasi (%)"] = (
    df_realisasi_belanja_penyedia_pelayanan["REALISASI BELANJA (RP)"] /
    df_realisasi_belanja_penyedia_pelayanan["ALOKASI BELANJA (RP)"] * 100
).round(2)
df_realisasi_belanja_penyedia_pelayanan["Tingkat Realisasi (%)"] = df_realisasi_belanja_penyedia_pelayanan["Tingkat Realisasi (%)"].astype(str) + "%"

## Realisasi belanja menurut Program ##
df_realisasi_belanja_program = df.groupby(["PR1", "TAHUN"], as_index=False)[
    ["ALOKASI BELANJA (RP)", "REALISASI BELANJA (RP)"]
].sum().rename(columns={"TAHUN": "Tahun", "PR1": "Program"})
df_realisasi_belanja_program["Realisasi Belanja"] = df_realisasi_belanja_program[
    "REALISASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_program["Alokasi Belanja"] = df_realisasi_belanja_program[
    "ALOKASI BELANJA (RP)"
].apply(format_rupiah_singkat)
df_realisasi_belanja_program["Tingkat Realisasi (%)"] = (
    df_realisasi_belanja_program["REALISASI BELANJA (RP)"] /
    df_realisasi_belanja_program["ALOKASI BELANJA (RP)"] * 100
).round(2)
df_realisasi_belanja_program["Tingkat Realisasi (%)"] = df_realisasi_belanja_program["Tingkat Realisasi (%)"].astype(str) + "%"

## Wilayah ##
page_wilayah = vm.Page(
    title="Wilayah Puskesmas",
    components=[  
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),  
            title="Distribusi Puskesmas dengan Realisasi Berdasarkan Efektivitas",
            components=[
                vm.Graph(
                    id="Pie Karakter Puskesmas",
                    figure=px.pie(
                        df_karakter_kategori,
                        names="Karakteristik",
                        values="Jumlah",
                        title="Berdasarkan Karakteristik"
                    )
                ),
                vm.Tabs(
                    tabs=[
                        vm.Container(
                            title="Provinsi",
                            components=[
                                vm.Graph(
                                    id="Pie Provinsi Puskesmas",
                                    figure=px.pie(
                                        df_provinsi_kategori,
                                        names="Provinsi",
                                        values="Jumlah",
                                        title="Berdasarkan Provinsi"
                                    )
                                ),
                            ],
                        ),
                        vm.Container(
                            title="Kabupaten/Kota",
                            components=[
                                vm.Graph(
                                    id="Pie Kabupaten/Kota Puskesmas",
                                    figure=px.pie(
                                        df_kabko_kategori,
                                        names="Kabupaten/Kota",
                                        values="Jumlah",
                                        title="Berdasarkan Kabupaten/Kota"
                                    )
                                ),
                            ],
                        ),
                    ],
                ),
            ]
        ),
        vm.Container(
            title="Tabel Detail Puskesmas",
            components=[
                vm.AgGrid(
                    id="Tabel Wilayah Puskesmas", 
                    figure=dash_ag_grid(
                        data_frame=df_wilayah_belanja[[
                            "Nama Puskesmas", "Kode Puskesmas", "Karakteristik", "Provinsi", "Kabupaten/Kota",
                            "Tahun", "Alokasi Belanja", "Realisasi Belanja", "Sisa Belanja", "Tingkat Realisasi (%)"
                        ]]
                    )
                )
            ]
        )
    ],
    controls=[
        vm.Filter(
            column="Karakteristik",
            targets=["Tabel Wilayah Puskesmas", "Pie Karakter Puskesmas"],
            selector=vm.Dropdown(value=["ALL"])
        ),
        vm.Filter(
            column="Provinsi",
            targets=["Tabel Wilayah Puskesmas", "Pie Provinsi Puskesmas"],
            selector=vm.Dropdown(value=["ALL"])
        ),
        vm.Filter(
            column="Kabupaten/Kota",
            targets=["Tabel Wilayah Puskesmas", "Pie Kabupaten/Kota Puskesmas"],
            selector=vm.Dropdown(value=["ALL"])
        ),
        vm.Filter(
            column="Tahun",
            targets=["Tabel Wilayah Puskesmas", "Pie Karakter Puskesmas", "Pie Provinsi Puskesmas", "Pie Kabupaten/Kota Puskesmas"],
            selector=vm.Dropdown(value=["ALL"])
        ),
        vm.Filter(
            column="Kategori Efektivitas",
            targets=["Pie Karakter Puskesmas", "Pie Provinsi Puskesmas", "Pie Kabupaten/Kota Puskesmas"],
            selector=vm.Dropdown(value=["ALL"])
        )
    ]
)

## Realisasi Belanja Menurut Sumber Pembiayaan ##
page_realisasi_belanja_sumber = vm.Page(
    title="Realisasi Belanja menurut Sumber Pembiayaan",
    components=[  
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),  
            components=[
                vm.Graph(
                    id="Pie Realisasi Belanja Sumber Pembiayaan",
                    figure=px.pie(
                        df_realisasi_belanja_sumber, 
                        values="REALISASI BELANJA (RP)", 
                        names="Sumber Pembiayaan",
                        title="Total Realisasi Belanja menurut Sumber Pembiayaan"
                    )
                ),
                vm.Graph(
                    id="Bar Realisasi Belanja Sumber Pembiayaan",
                    figure=px.bar(
                        df_realisasi_belanja_sumber,
                        y="Sumber Pembiayaan",
                        x="Tingkat Realisasi (%)",
                        color="Tingkat Realisasi (%)",
                        orientation="h",
                        title="Tingkat Realisasi Belanja menurut Sumber Pembiayaan"
                    )
                )
            ],
        ),
        vm.Container(
            components=[
                vm.AgGrid(
                    id="Tabel Realisasi Belanja Sumber Pembiayaan", 
                    figure=dash_ag_grid(
                        data_frame=df_realisasi_belanja_sumber[[
                            "Sumber Pembiayaan", "Tahun", "Alokasi Belanja", "Realisasi Belanja"
                        ]],
                    )
                ),
            ],
        )
    ],
    controls=[
        vm.Filter(
            column="Sumber Pembiayaan",
            targets=["Pie Realisasi Belanja Sumber Pembiayaan", "Tabel Realisasi Belanja Sumber Pembiayaan", "Bar Realisasi Belanja Sumber Pembiayaan"],
            selector=vm.Dropdown(value=["ALL"])
        ),
        vm.Filter(
            column="Tahun",
            targets=["Pie Realisasi Belanja Sumber Pembiayaan", "Tabel Realisasi Belanja Sumber Pembiayaan", "Bar Realisasi Belanja Sumber Pembiayaan"],
            selector=vm.Dropdown(value=["ALL"])
        ),
    ]
)

## Realisasi Belanja Menurut Pengelola Anggaran ##
page_realisasi_belanja_pengelola_anggaran = vm.Page(
    title="Realisasi Belanja menurut Pengelola Anggaran",
    components=[  
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),  
            components=[
                vm.Graph(
                    id="Pie Realisasi Belanja Pengelola Anggaran",
                    figure=px.pie(
                        df_realisasi_belanja_pengelola_anggaran, 
                        values="REALISASI BELANJA (RP)", 
                        names="Pengelola Anggaran",
                        title="Total Realisasi Belanja menurut Pengelola Anggaran"
                    )
                ),
                vm.Graph(
                    id="Bar Realisasi Belanja Pengelola Anggaran",
                    figure=px.bar(
                        df_realisasi_belanja_pengelola_anggaran,
                        y="Pengelola Anggaran",
                        x="Tingkat Realisasi (%)",
                        color="Tingkat Realisasi (%)",
                        orientation="h",
                        title="Tingkat Realisasi Belanja menurut Pengelola Anggaran"
                    )
                )
            ],
        ),
        vm.Container(
            components=[
                vm.AgGrid(
                    id="Tabel Realisasi Belanja Pengelola Anggaran", 
                    figure=dash_ag_grid(
                        data_frame=df_realisasi_belanja_pengelola_anggaran[[
                            "Pengelola Anggaran", "Tahun", "Alokasi Belanja", "Realisasi Belanja"
                        ]],
                    )
                ),
            ],
        )
    ],
    controls=[
        vm.Filter(column="Pengelola Anggaran", targets=[
            "Pie Realisasi Belanja Pengelola Anggaran", "Tabel Realisasi Belanja Pengelola Anggaran", "Bar Realisasi Belanja Pengelola Anggaran"
        ], 
        selector=vm.Dropdown(value=["ALL"])),
        vm.Filter(column="Tahun", targets=[
            "Pie Realisasi Belanja Pengelola Anggaran", "Tabel Realisasi Belanja Pengelola Anggaran", "Bar Realisasi Belanja Pengelola Anggaran"
        ], 
        selector=vm.Dropdown(value=["ALL"]))
    ]
)

## Realisasi belanja menurut Penyedia Pelayanan ##
page_realisasi_belanja_penyedia_pelayanan = vm.Page(
    title="Realisasi Belanja menurut Penyedia Pelayanan",
    components=[  
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),  
            components=[
                vm.Graph(
                    id="Pie Realisasi Belanja Penyedia Pelayanan",
                    figure=px.pie(
                        df_realisasi_belanja_penyedia_pelayanan, 
                        values="REALISASI BELANJA (RP)", 
                        names="Penyedia Pelayanan",
                        title="Total Realisasi Belanja menurut Penyedia Pelayanan"
                    )
                ),
                vm.Graph(
                    id="Bar Realisasi Belanja Penyedia Pelayanan",
                    figure=px.bar(
                        df_realisasi_belanja_penyedia_pelayanan,
                        y="Penyedia Pelayanan",
                        x="Tingkat Realisasi (%)",
                        color="Tingkat Realisasi (%)",
                        orientation="h",
                        title="Tingkat Realisasi Belanja menurut Penyedia Pelayanan"
                    )
                )
            ],
        ),
        vm.Container(
            components=[
                vm.AgGrid(
                    id="Tabel Realisasi Belanja Penyedia Pelayanan", 
                    figure=dash_ag_grid(
                        data_frame=df_realisasi_belanja_penyedia_pelayanan[[
                            "Penyedia Pelayanan", "Tahun", "Alokasi Belanja", "Realisasi Belanja"
                        ]],
                    )
                ),
            ],
        )
    ],
    controls=[
        vm.Filter(column="Penyedia Pelayanan", targets=[
            "Pie Realisasi Belanja Penyedia Pelayanan", "Tabel Realisasi Belanja Penyedia Pelayanan", "Bar Realisasi Belanja Penyedia Pelayanan"
        ], 
        selector=vm.Dropdown(value=["ALL"])),
        vm.Filter(column="Tahun", targets=[
            "Pie Realisasi Belanja Penyedia Pelayanan", "Tabel Realisasi Belanja Penyedia Pelayanan", "Bar Realisasi Belanja Penyedia Pelayanan"
        ], 
        selector=vm.Dropdown(value=["ALL"]))
    ]
)

## Realisasi belanja menurut Program ##
page_realisasi_belanja_program = vm.Page(
    title="Realisasi Belanja menurut Program",
    components=[  
        vm.Container(
            layout=vm.Grid(grid=[[0, 1]]),  
            components=[
                vm.Graph(
                    id="Pie Realisasi Belanja Program",
                    figure=px.pie(
                        df_realisasi_belanja_program, 
                        values="REALISASI BELANJA (RP)", 
                        names="Program",
                        title="Total Realisasi Belanja menurut Program"
                    )
                ),
                vm.Graph(
                    id="Bar Realisasi Belanja Program",
                    figure=px.bar(
                        df_realisasi_belanja_program,
                        y="Program",
                        x="Tingkat Realisasi (%)",
                        color="Tingkat Realisasi (%)",
                        orientation="h",
                        title="Tingkat Realisasi Belanja menurut Program"
                    )
                )
            ],
        ),
        vm.Container(
            components=[
                vm.AgGrid(
                    id="Tabel Realisasi Belanja Program", 
                    figure=dash_ag_grid(
                        data_frame=df_realisasi_belanja_program[[
                            "Program", "Tahun", "Alokasi Belanja", "Realisasi Belanja"
                        ]],
                    )
                ),
            ],
        )
    ],
    controls=[
        vm.Filter(column="Program", targets=[
            "Pie Realisasi Belanja Program", "Tabel Realisasi Belanja Program", "Bar Realisasi Belanja Program"
        ], 
        selector=vm.Dropdown(value=["ALL"])),
        vm.Filter(column="Tahun", targets=[
            "Pie Realisasi Belanja Program", "Tabel Realisasi Belanja Program", "Bar Realisasi Belanja Program"
        ], 
        selector=vm.Dropdown(value=["ALL"]))
    ]
)

# Buat dashboard
dashboard = vm.Dashboard(pages=[
    page_wilayah,
    page_realisasi_belanja_sumber,
    page_realisasi_belanja_pengelola_anggaran,
    page_realisasi_belanja_penyedia_pelayanan,
    page_realisasi_belanja_program,
],
navigation=vm.Navigation(pages={
            "Puskesmas": [
                "Wilayah Puskesmas"
            ],
            "Realisasi": [
                "Realisasi Belanja menurut Sumber Pembiayaan", 
                "Realisasi Belanja menurut Pengelola Anggaran", 
                "Realisasi Belanja menurut Penyedia Pelayanan", 
                "Realisasi Belanja menurut Program"
            ],
        }
    ),
)

# Buat dan jalankan aplikasi
Vizro().build(dashboard).run()
