import React, { useEffect, useRef, useState } from "react";

function encodeToBase64(str) {
  return window.btoa(unescape(encodeURIComponent(str)));
}

// draw.io 로딩 전에 아래 함수 추가
function extractPureXml(xml) {
  // diagram 태그가 있다면 내부 mxGraphModel 부분만 추출
  const match = xml.match(/<mxGraphModel[^>]*>[\s\S]*<\/mxGraphModel>/);
  return match ? match[0] : ""; // 없으면 그대로 반환
}

function FridgeEditor() {
  const iframeRef = useRef(null);
  const [xmlData, setXmlData] = useState("");

  // 1. fridge XML 불러오기
  console.log("✅ FridgeEditor 컴포넌트가 로딩됨");
  useEffect(() => {
    fetch("http://localhost:8000/fridge/bbox/xml")
      .then((res) => res.text())
      .then((xml) => {
        console.log("📦 XML 데이터 (실제):", xml);
        setXmlData(xml);
      });
  }, []);

  // 2. iframe에 XML 로딩
 useEffect(() => {
  if (!xmlData || !iframeRef.current) return;

  const iframe = iframeRef.current;

  const loadXml = () => {
    const cleanXml = extractPureXml(xmlData); // diagram 제거
    const encodedXml = encodeToBase64(cleanXml);
    
    console.log("🧾 Base64로 인코딩된 XML:", encodedXml);
    console.log("🧾 실제 전달할 XML:", cleanXml);
    console.log("🚀 draw.io에 XML 강제 로딩 시도...");
    iframe.contentWindow.postMessage(
      JSON.stringify({
        action: "load",
        autosave: 1,
        xml: cleanXml,
        format: "xml"
      }),
      "*"
    );
    console.log("📤 draw.io에 보낼 메시지:", {
      action: "load",
      autosave: 1,
      xml: cleanXml,
      format: "xml"
    });

    // ⏱️ 0.5초 뒤 자동 리센터링 요청
    setTimeout(() => {
      iframe.contentWindow.postMessage(
        JSON.stringify({
          action: "fit",
        }),
        "*"
      );
    }, 500);
  };

  // ✅ configure 이벤트 기반
 // 이 부분의 listener 함수 수정
const listener = (event) => {
  let data;
  try {
    data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
  } catch (err) {
    return;
  }

  if (data.event === "configure") {
    console.log("✅ draw.io iframe이 ready 상태 됨");
    loadXml(); // 여기서 draw.io에 xml 로드 시도
  }
};


  // ✅ configure가 안 오면 1초 후 강제 로딩 시도
  const timeout = setTimeout(() => {
    console.warn("⏱️ configure 이벤트 지연 — 수동 로딩 시도 중");
    loadXml();
  }, 1000);

  window.addEventListener("message", listener);
  return () => {
    window.removeEventListener("message", listener);
    clearTimeout(timeout);
  };
}, [xmlData]);



  // 3. export 버튼 동작
  const handleExport = () => {
   iframeRef.current.contentWindow.postMessage(
      JSON.stringify({ action: "export", format: "xml" }),
      "*"
    );
  };

  // 4. 수정된 XML 받기
  useEffect(() => {
    const receive = (event) => {
    let data;
    try {
      data = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
    } catch (err) {
      return;
    }

    if (data.event === "export") {
      console.log("📝 수정된 XML:", data.data);
    }
  };

    window.addEventListener("message", receive);
    return () => window.removeEventListener("message", receive);
  }, []);

  return (
    <div>
      <h2>🧊 냉장고 편집기 </h2>
      <button onClick={handleExport}>📤 수정된 상태 가져오기</button>
      <iframe
        ref={iframeRef}
        title="DrawIO Fridge"
        src="https://embed.diagrams.net/?embed=1&proto=json&ui=min"
        width="100%"
        height="700px"
        frameBorder="0"
      />
    </div>
  );
}

export default FridgeEditor;
