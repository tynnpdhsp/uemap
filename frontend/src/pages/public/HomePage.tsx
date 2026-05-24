import React from "react";
import { useAuth } from "../../context/AuthContext";

export const HomePage: React.FC = () => {
  const { student, isAuthenticated } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-grow w-full flex flex-col">
        {/* Banner chào mừng */}
        <div className="mb-8 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 p-8 text-white shadow-lg">
          <h1 className="text-3xl font-extrabold tracking-tight md:text-4xl">
            Bản đồ Sinh viên Sư phạm HCMUE
          </h1>
          <p className="mt-2 text-blue-100 max-w-xl text-sm md:text-base">
            Hệ thống quản lý vị trí sinh viên, tìm kiếm bạn bè, phòng trọ, địa điểm ăn uống xung quanh trường Đại học Sư phạm TP.HCM.
          </p>
          {isAuthenticated ? (
            <div className="mt-4 inline-flex items-center px-4 py-2 bg-white text-blue-600 rounded-lg font-bold text-sm shadow">
              Chào mừng quay trở lại, {student?.full_name}!
            </div>
          ) : (
            <div className="mt-4 text-sm font-semibold text-blue-200">
              Đăng nhập để cập nhật vị trí của bạn trên bản đồ.
            </div>
          )}
        </div>

        {/* Map Container / Skeleton Map */}
        <div className="flex-grow grid grid-cols-1 lg:grid-cols-4 gap-8 min-h-[400px]">
          {/* Side panel */}
          <div className="lg:col-span-1 bg-white p-6 rounded-2xl shadow-md border border-gray-100 flex flex-col justify-between">
            <div>
              <h2 className="text-lg font-bold text-gray-800 border-b border-gray-100 pb-3 mb-4">Địa điểm quanh trường</h2>
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-100 flex items-center space-x-3 cursor-pointer hover:bg-blue-100 transition">
                  <span className="h-2.5 w-2.5 rounded-full bg-blue-600"></span>
                  <span className="text-sm font-medium text-blue-800">Cơ sở 1 - An Dương Vương</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center space-x-3 cursor-pointer hover:bg-gray-100 transition">
                  <span className="h-2.5 w-2.5 rounded-full bg-gray-400"></span>
                  <span className="text-sm font-medium text-gray-700">Cơ sở 2 - Lê Văn Sỹ</span>
                </div>
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex items-center space-x-3 cursor-pointer hover:bg-gray-100 transition">
                  <span className="h-2.5 w-2.5 rounded-full bg-gray-400"></span>
                  <span className="text-sm font-medium text-gray-700">Ký túc xá sinh viên</span>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-gray-100 text-xs text-gray-400">
              Bản đồ thử nghiệm tích hợp OpenStreetMap & LeafletJS.
            </div>
          </div>

          {/* Map canvas mockup */}
          <div className="lg:col-span-3 bg-white rounded-2xl shadow-md border border-gray-100 relative overflow-hidden flex flex-col items-center justify-center p-8 text-center min-h-[350px]">
            <div className="absolute inset-0 bg-blue-50 bg-[radial-gradient(#3b82f6_1px,transparent_1px)] [background-size:16px_16px] opacity-40"></div>
            <div className="relative z-10 max-w-sm">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-600 mb-4 animate-bounce">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-gray-800 mb-1">Bản đồ đang tải...</h3>
              <p className="text-sm text-gray-500">
                LeafletJS Map đang được khởi tạo tại tọa độ Cơ sở 1 (10.7599° N, 106.6787° E)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
