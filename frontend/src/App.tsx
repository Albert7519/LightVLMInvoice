import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, FileText, CheckCircle, FileSpreadsheet, Loader } from 'lucide-react';

// Read API base from environment variables (VITE_API_BASE)
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api/v1/invoices';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [fileUrl, setFileUrl] = useState<string>('');
  const [taskId, setTaskId] = useState<string>('');
  const [status, setStatus] = useState<string>('');
  const [progress, setProgress] = useState<number>(0);
  const [result, setResult] = useState<any>(null);
  const [message, setMessage] = useState<string>('');

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (f: File) => {
    setFile(f);
    setFileUrl(URL.createObjectURL(f));
    setResult(null);
    setStatus('');
    setProgress(0);
    setTaskId('');
  };

  const uploadFile = async () => {
    if (!file) return;
    setStatus('UPLOADING');
    setMessage('正在上传发票源文件...');
    
    const formData = new FormData();
    formData.append('files', file);

    try {
      const res = await axios.post(`${API_BASE}/extract`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      if (res.data.data.task_ids.length > 0) {
        setTaskId(res.data.data.task_ids[0]);
        setStatus('PROCESSING');
      }
    } catch (err) {
      console.error(err);
      setStatus('FAILED');
      setMessage('上传失败，请检查后端运行状态。');
    }
  };

  // 轮询任务状态
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (taskId && status === 'PROCESSING') {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`${API_BASE}/status/${taskId}`);
          const data = res.data;
          if (data.status === 'COMPLETED') {
            setStatus('COMPLETED');
            setProgress(100);
            setResult(data.result);
            setMessage('提取完毕！');
            clearInterval(interval);
          } else if (data.status === 'PROCESSING') {
            setProgress(data.progress);
            setMessage(data.message || '大模型正在解析中...');
          } else if (data.status === 'FAILED') {
            setStatus('FAILED');
            setMessage('解析失败。');
            clearInterval(interval);
          }
        } catch (error) {
          console.error(error);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, status]);

  const exportExcel = async () => {
    if (!result) return;
    try {
      const res = await axios.post(`${API_BASE}/export`, [result], {
        responseType: 'blob'
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'invoice_export.xlsx');
      document.body.appendChild(link);
      link.click();
    } catch (err) {
      console.error(err);
      alert("导出失败");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#1a1c29] to-black p-8 text-slate-200 font-sans">
      <header className="max-w-7xl mx-auto mb-12 text-center space-y-4">
        <h1 className="text-4xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-500 tracking-tight">
          AI 多模态混合发票识别系统
        </h1>
        <p className="text-lg text-slate-400 font-medium">Qwen3.5 VLM 底座驱动 · 跨国语言 · 混合版式无定型解析</p>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* 左侧：上传与源文档预览区 */}
        <div className="glass-panel p-6 flex flex-col h-[75vh]">
          <h2 className="text-xl items-center flex font-semibold mb-4 text-blue-300">
            <FileText className="mr-2" />
            原件预览
          </h2>
          
          {!file ? (
            <div 
              onDragOver={onDragOver} 
              onDrop={onDrop}
              className="flex-1 border-2 border-dashed border-slate-600 rounded-xl flex flex-col items-center justify-center hover:border-blue-400 hover:bg-slate-800/50 transition-all cursor-pointer group"
            >
              <UploadCloud size={64} className="text-slate-500 group-hover:text-blue-400 mb-4 transition-colors" />
              <p className="text-xl font-medium text-slate-300 group-hover:text-white mb-2">拖拽 PDF 或 图像 到此处</p>
              <p className="text-sm text-slate-500">支持 .pdf .jpg .png .webp 多页混合上传</p>
              <label className="mt-6 px-6 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg cursor-pointer transition-colors shadow-lg shadow-blue-500/30">
                浏览文件
                <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => e.target.files && handleFileSelected(e.target.files[0])} />
              </label>
            </div>
          ) : (
            <div className="flex-1 flex flex-col relative rounded-xl overflow-hidden border border-slate-700 bg-slate-800/50">
               {file.type === 'application/pdf' ? (
                 <iframe src={fileUrl} className="w-full h-full" title="PDF Preview" />
               ) : (
                 <img src={fileUrl} alt="Preview" className="w-full h-full object-contain" />
               )}
               
               {/* 控制浮层 */}
               <div className="absolute bottom-4 left-0 right-0 flex justify-center space-x-4">
                  <button onClick={() => setFile(null)} className="px-4 py-2 bg-slate-700/80 hover:bg-slate-600 backdrop-blur text-sm rounded-lg transition-colors">更换文稿</button>
                  {status === '' && (
                    <button onClick={uploadFile} className="px-4 py-2 bg-indigo-600/90 hover:bg-indigo-500 backdrop-blur text-sm rounded-lg shadow-xl shadow-indigo-500/30 transition-colors flex items-center">
                      <CheckCircle className="w-4 h-4 mr-2" />
                      开始 AI 智能识别
                    </button>
                  )}
               </div>
            </div>
          )}
        </div>

        {/* 右侧：状态与表单结构结果 */}
        <div className="glass-panel p-6 flex flex-col h-[75vh] relative">
           <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-emerald-300 flex items-center">
                <CheckCircle className="mr-2" />
                提取结果 (双屏对校)
              </h2>
              {result && (
                <button onClick={exportExcel} className="flex items-center text-sm px-4 py-2 bg-emerald-600/20 text-emerald-300 border border-emerald-500/50 rounded-lg hover:bg-emerald-600/40 transition-colors">
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  导出 Excel
                </button>
              )}
           </div>

           {!taskId && !result && (
             <div className="flex-1 flex items-center justify-center text-slate-500">
               等待任务触发...
             </div>
           )}

           {(status === 'PROCESSING' || status === 'UPLOADING') && (
             <div className="flex-1 flex flex-col items-center justify-center space-y-6">
               <Loader className="w-12 h-12 text-blue-400 animate-spin" />
               <div className="w-3/4 bg-slate-700 rounded-full h-2.5 overflow-hidden">
                 <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2.5 rounded-full transition-all duration-500 ease-out" style={{ width: `${Math.max(progress, 5)}%` }}></div>
               </div>
               <p className="text-blue-300 animate-pulse font-medium">{message || '加载中...'}</p>
             </div>
           )}

           {status === 'FAILED' && (
             <div className="flex-1 flex flex-col items-center justify-center space-y-6 text-red-400">
               <div className="text-2xl font-bold">⚠️ 处理失败</div>
               <p>{message}</p>
             </div>
           )}

           {result && (
             <div className="flex-1 overflow-y-auto space-y-6 custom-scrollbar pr-2">
               <div className="grid grid-cols-2 gap-4">
                 <Field label="发票号码" value={result.invoice_data?.invoice_number} />
                 <Field label="发票日期" value={result.invoice_data?.invoice_date} />
                 <Field label="总计金额" value={`${result.invoice_data?.currency || ''} ${result.invoice_data?.total_amount || ''}`} />
                 <Field label="销方/商家" value={result.invoice_data?.vendor_name} />
                 <Field label="购买方" value={result.invoice_data?.purchaser_name} className="col-span-2" />
               </div>

               {result.invoice_data?.items && result.invoice_data.items.length > 0 && (
                 <div className="mt-8">
                   <h3 className="text-slate-400 text-sm font-semibold mb-3 border-b border-slate-700 pb-2">明细清单</h3>
                   <table className="w-full text-left text-sm">
                     <thead className="bg-slate-800/50 text-slate-400">
                       <tr>
                         <th className="px-4 py-2 rounded-tl-lg">描述</th>
                         <th className="px-4 py-2">数量</th>
                         <th className="px-4 py-2">单价</th>
                         <th className="px-4 py-2 rounded-tr-lg">金额</th>
                       </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-700">
                       {result.invoice_data.items.map((item: any, i: number) => (
                         <tr key={i} className="hover:bg-slate-800/30 transition-colors">
                           <td className="px-4 py-3">{item.description || '-'}</td>
                           <td className="px-4 py-3">{item.quantity || '-'}</td>
                           <td className="px-4 py-3">{item.unit_price || '-'}</td>
                           <td className="px-4 py-3 font-medium text-emerald-400">{item.amount || '-'}</td>
                         </tr>
                       ))}
                     </tbody>
                   </table>
                 </div>
               )}
             </div>
           )}
        </div>

      </main>
    </div>
  );
}

function Field({ label, value, className = '' }: { label: string, value: string | undefined, className?: string }) {
  return (
    <div className={`p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-blue-500/30 transition-colors ${className}`}>
      <div className="text-xs text-slate-400 font-medium mb-1">{label}</div>
      <div className="text-slate-100 font-semibold truncate">{value || <span className="text-slate-600 italic">未提取</span>}</div>
    </div>
  );
}

export default App;
