import React, { useEffect, useState } from "react";

function App() {
  const [apiStatus, setApiStatus] = useState<string>("Đang kiểm tra...");

  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => {
        if (data.success && data.data?.status === "ok") {
          setApiStatus("Hoạt động bình thường");
        } else {
          setApiStatus("Lỗi phản hồi API");
        }
      })
      .catch((err) => {
        console.error(err);
        setApiStatus("Không thể kết nối đến API");
      });
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <header className="bg-blue-600 text-white shadow-md py-4 px-6">
        <h1 className="text-xl font-bold">Bản đồ sinh viên sư phạm (HCMUE)</h1>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">
            Sprint 1 - Nền tảng
          </h2>
          <p className="text-gray-600 mb-6">
            Môi trường phát triển và skeleton ứng dụng đã được khởi tạo thành
            công theo kiến trúc tổng thể.
          </p>

          <div className="border-t border-gray-200 pt-6">
            <h3 className="font-semibold text-gray-700 mb-2">
              Trạng thái kết nối API:
            </h3>
            <span
              className={`inline-block px-4 py-2 rounded-full font-bold text-sm ${
                apiStatus.includes("OK")
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {apiStatus}
            </span>
          </div>
        </div>
      </main>

      <footer className="bg-gray-800 text-white text-center py-4 text-sm">
        &copy; 2026 Nguyễn Ngọc Phú Tỷ - Nhập môn DevOps. Bảo lưu mọi quyền.
      </footer>
    </div>
  );
}

export default App;
