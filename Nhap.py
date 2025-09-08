import json

# Load dữ liệu JSON một lần
with open("data/materials.json", "r", encoding="utf-8") as f:
    materials = json.load(f)

with open("data/then_standard.json", "r", encoding="utf-8") as f:
    then_data = json.load(f)
#Hàm phụ trợ tự vấn kết quả
def tu_van_dieu_chinh(d, l, sf_tb):
    """
    Tư vấn điều chỉnh d hoặc l để hệ số an toàn về khoảng 1.5–2
    sf_tb: hệ số an toàn trung bình của vật liệu đang xét
    """
    tu_van = ""
    if sf_tb < 1.5:
        he_so = 1.5 / sf_tb  # cần tăng diện tích chịu lực
        d_moi = round(d * he_so**0.5, 1)
        l_moi = round(l * he_so**0.5, 1)
        tu_van = (f"Hệ số an toàn thấp ({sf_tb:.2f}). "
                  f"Có thể tăng đường kính lên khoảng {d_moi} mm "
                  f"hoặc tăng chiều dài then lên khoảng {l_moi} mm.")
    elif sf_tb > 2:
        he_so = 2 / sf_tb  # có thể giảm diện tích chịu lực
        d_moi = round(d * he_so**0.5, 1)
        l_moi = round(l * he_so**0.5, 1)
        tu_van = (f"Hệ số an toàn cao ({sf_tb:.2f}). "
                  f"Có thể giảm đường kính xuống khoảng {d_moi} mm "
                  f"hoặc giảm chiều dài then xuống khoảng {l_moi} mm.")
    else:
        tu_van = "Thiết kế đã tối ưu, không cần điều chỉnh."
    return tu_van
def tu_van_tk(d, l, T, b, h, t1, sigma, tau):
    """
    Tìm ra giới hạn min <= d <= max
    d: đường kính tính toán
    l: chiều dài trục tính toán

    """
    d_trai = max(3*T/(l*(h-t1)*sigma), 3*T/(l*b*tau))
    d_phai = min(4*T/(l*(h-t1)*sigma), 4*T/(l*b*tau))
    d_tb = round((d_trai+d_phai)/2)
    return d_tb

#Hàm tính toán chính
def tinh_toan_key(d, l, p, n, eta, z, mat1, mat2):
    """
    Hàm tính toán then
    d: đường kính trục (mm)
    l: chiều dài trục (mm)
    p: công suất (kW)
    n: tốc độ quay (vòng/phút)
    eta: hiệu suất truyền
    z: số then
    mat1, mat2: tên vật liệu
    """
    
    #---Lấy data----
    # Tra kích thước then trong bảng then_data
    b, h, t1, t2 = None, None, None, None
    for item in then_data:
        if item["d_min"] < d <= item["d_max"]:
            b, h, t1, t2 = item["b"], item["h"], item["t1"], item["t2"]
            break

    if b is None or h is None:
        return {"Error": f"Đường kính {d} mm nằm ngoài phạm vi tính toán trong bảng then."}

    # Tra σ của vật liệu
    sigma1 = next((m["sigma"] for m in materials if m["name"] == mat1), None)
    sigma2 = next((m["sigma"] for m in materials if m["name"] == mat2), None)

    #---Tính toán----
    # Moment xoắn (Nm)
    try:
        T = 30000 * p * eta / (3.1416 *n*z)
    except ZeroDivisionError:
        return {"error": "Tốc độ quay cần lớn hơn 0"}
    
    # Chiều dài then
    l_then = 0.8 * l

    # Tính ứng suất trên then
    sigma_dap = 2*T/(d*l*(h-t1))
    tau = 2*T/(d*l*b)

    # Tính ứng suất cho phép
    sigma1_cp = sigma1 / 3.5
    tau1_cp = sigma1_cp / 2
    sigma2_cp = sigma2 / 3.5
    tau2_cp = sigma2_cp / 2

    #Tính sf theo vật liệu
    sf11 = sigma1_cp / sigma_dap
    sf12 = tau1_cp / tau
    sf21 = sigma2_cp / sigma_dap
    sf22 = tau2_cp / tau

    #---Đánh giá thiết kế ---
    if 1.5 <= sf11 <= 2 and 1.5 <= sf12 <=2:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} đã hợp lý")
    elif sf11 < 1.5 or sf12 < 1.5:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} không đủ bền")
    elif sf11 > 2 and sf12 > 2:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} thừa bền")
    else:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} chưa tối ưu")
    if 1.5 <= sf21 <= 2 and 1.5 <= sf22 <=2:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} đã hợp lý")
    elif sf21 < 1.5 or sf22 < 1.5:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} không đủ bền")
    elif sf21 > 2 and sf22 > 2:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} thừa bền")
    else:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} chưa tối ưu")
    
    #Tư vấn tối ưu thiết kế
    # Tìm giá trị tối ưu
    d_tv1 = tu_van_tk(d, l, T, b, h, t1, sigma1_cp,tau1_cp)
    d_tv2 = tu_van_tk(d, l, T, b, h, t1, sigma2_cp,tau2_cp)
    sf_tb1 = (sf11 + sf12) / 2
    sf_tb2 = (sf21 + sf22) / 2

    # Gợi ý điều chỉnh
    tu_van1 = f"Đường kính tối ưu có thể là {d_tv1}"
    tu_van2 = tu_van_dieu_chinh(d, l, sf_tb2)
    print(tu_van1)
    
    # Trả kết quả
    return {
        # Input
        "d": d,
        "l": l,
        "p": p,
        "n": n,
        "eta": eta,
        "z": z,
        "mat1": mat1,
        "mat2": mat2,
        # Output
        "T": round(T, 2),
        "b": b,
        "h": h,
        "t1": t1,
        "t2": t2,
        "l_then": l_then,
        "sigma_dap": sigma_dap,
        "tau": tau,
        "sigma1": sigma1,
        "sigma2": sigma2,
        "sf11": sf11,
        "sf12": sf12,
        "sf21": sf21,
        "sf22": sf22,
        "danh_gia1": danh_gia1,
        "danh_gia2": danh_gia2,
        "d_tv1": d_tv1,
        "tu_van1": tu_van1,
        "tu_van2": tu_van2
    }
demo = tinh_toan_key(26,50,5,40,90,1,"C45","40Cr")
print(demo)
