import json

# Load dữ liệu JSON một lần
with open("data/materials.json", "r", encoding="utf-8") as f:
    materials = json.load(f)

with open("data/then_standard.json", "r", encoding="utf-8") as f:
    then_data = json.load(f)

#Hàm tính toán chính
def tinh_toan_key(d, L, p, n, eta, z, mat1, mat2):
    """
    Hàm tính toán then
    d: đường kính trục (mm)
    L: chiều dài trục (mm)
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
        T = 300000 * p * eta / (3.1416 *n*z)
    except ZeroDivisionError:
        return {"error": "Tốc độ quay lớn hơn 0"}
    
    # Chiều dài then
    l = 0.8 * L

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
    #---Vật liệu mat1
    if 1.5 <= sf11 <= 2 and 1.5 <= sf12:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} đã tối ưu")
    elif sf11 < 1.5 or sf12 < 1.5:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} không đủ bền")
    elif sf11 > 2 and sf12 > 2:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} thừa bền")
    else:
        danh_gia1 = str(f"Thiết kế then sử dụng vật liệu {mat1} chưa tối ưu")
    #---Vật liệu mat2
    if 1.5 <= sf21 <= 2 and 1.5 <= sf22:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} đã tối ưu")
    elif sf21 < 1.5 or sf22 < 1.5:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} không đủ bền")
    elif sf21 > 2 and sf22 > 2:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} thừa bền")
    else:
        danh_gia2 = str(f"Thiết kế then sử dụng vật liệu {mat2} chưa tối ưu")
    
   
    # Trả kết quả
    return {
        # Input
        "d": d,
        "L": L,
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
        "l": l,
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
       
    }
# Hàm tư vấn thiết kế
def tu_van_dieu_chinh(d, L, p, n, eta, z, mat1, mat2):
    # Kết quả gốc
    res = tinh_toan_key(d, L, p, n, eta, z, mat1, mat2)
    #Chiều dài then
    l = 0.8*L
    # Vật liệu mat1
    # Nếu đã đạt yêu cầu thì OK
    if 1.5 <= res["sf11"] <= 2 and res["sf12"] >= 1.5:
        return f"Thiết kế sử dụng vật liệu {mat1} đạt yêu cầu, không cần điều chỉnh."
    
    giai_phap_d = None
    giai_phap_l = None
    # ===== 1. Thử tăng đường kính (giữ nguyên l) =====
    d_new = int(d) + 1
    while d_new <= int(1.5 * d):
        res_new = tinh_toan_key(d_new, l, p, n, eta, z, mat1, mat2)
        if res_new["sf11"] >= 1.5 and res_new["sf21"] >= 1.5:
            giai_phap_d = f"Khi sử dụng vật liệu {mat1} nên tăng đường kính trục lên {d_new} mm để đảm bảo đủ bền."
            break
        d_new += 1

    # Nếu vượt giới hạn 1.5d mà vẫn chưa đạt
    # => gợi ý kết hợp tăng đường kính + chiều dài
    if d_new > int(1.5 * d):
        giai_phap_d = f"Trong phạm vi đường kính từ d = {d} đến 1.5×d ={int(1.5*d)} mm, không có giá trị nào phù hợp. " \
               f"Hãy thử kết hợp tăng đường kính và chiều dài then và tính toán lại."

    # ===== 2. Thử tăng chiều dài (giữ nguyên d) =====
    l_new = int(l) + 5
    while l_new <= int(2 * l):
        res_new = tinh_toan_key(d, l_new, p, n, eta, z, mat1, mat2)
        if res_new["sf11"] >= 1.5 and res_new["sf21"] >= 1.5:
            giai_phap_l = f"Nên tăng chiều dài then lên {l_new} mm để đảm bảo sf11 và sf21 ≥ 1.5."
            break
        l_new += 5

    # Nếu vượt giới hạn 2l mà vẫn chưa đạt
    if l_new > int(2* d):
        giai_phap_l = f"Trong phạm vi chiều dài then l = {l} đến 2l ={int(2*l)} mm, không có giá trị nào phù hợp. " \
            f"Hãy thử kết hợp tăng đường kính và chiều dài then và tính toán lại."
 
    return giai_phap_l,giai_phap_d
demo = tu_van_dieu_chinh(40,60,5,40,97,1,"C45","C60")
for i in range(len(demo)):
    print(demo[i])