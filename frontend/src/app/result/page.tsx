'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense } from 'react';

// 내용 보여주는 컴포넌트
function ResultContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const imageUrl = searchParams.get('img');

    // 이미지 다운로드 함수 추가
    const handleDownload = async () => {
        if (!imageUrl) return;

        try {
            const response = await fetch(imageUrl);
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `pimfy_profile_${Date.now()}.jpg`; // 파일명 지정
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("다운로드 실패:", error);
            // 에러 발생 시 최후의 수단으로 새 창에서 이미지 열기
            window.open(imageUrl, '_blank');
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center bg-pink-50 p-4">
            <div className="w-full max-w-lg bg-white rounded-3xl shadow-xl overflow-hidden p-6 flex flex-col items-center">
                <h1 className="font-kyobo text-3xl text-center text-gray-800 mb-6">
                    <span className="text-brand-pink">♥</span> 핌피 프로필 도착 <span className="text-brand-pink">♥</span>
                </h1>

                <div className="w-full rounded-2xl overflow-hidden shadow-sm border border-gray-100 mb-6 bg-gray-50 min-h-[300px] flex items-center justify-center">
                    {imageUrl ? (
                        <img src={imageUrl} alt="공유된 프로필" className="w-full h-auto object-contain" />
                    ) : (
                        <p className="font-kyobo text-gray-400">이미지를 불러올 수 없어요 🥲</p>
                    )}
                </div>

                {/* ✅ 이미지 저장 버튼 추가 */}
                {imageUrl && (
                    <button
                        onClick={handleDownload}
                        className="font-kyobo w-full bg-white border-2 border-brand-pink text-brand-pink text-xl py-3 rounded-full shadow-md hover:bg-pink-50 transition-all mb-4 flex items-center justify-center gap-2"
                    >
                        💾 이미지 저장하기
                    </button>
                )}

                <p className="font-kyobo text-center text-gray-600 mb-6 leading-relaxed">
                    세상에 하나뿐인 우리 아이 AI 프로필!<br />
                    지금 바로 만들어보세요 🐾
                </p>

                <button
                    onClick={() => router.push('/')}
                    className="font-kyobo w-full bg-brand-pink text-white text-xl py-4 rounded-full shadow-lg hover:bg-opacity-90 transition-transform transform hover:scale-105 active:scale-95"
                >
                    나도 만들러 가기 👉
                </button>
            </div>
        </div>
    );
}
export default function ResultPage() {
    return (
        <Suspense fallback={<div className="flex min-h-screen items-center justify-center">로딩 중...</div>}>
            <ResultContent />
        </Suspense>
    );
}
