import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, CheckCircle, Loader, FileSpreadsheet, PlusCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1/invoices';

interface TaskState {
  status: string;
  progress: number;
  message: string;
  result: any;
}

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [taskIds, setTaskIds] = useState<string[]>([]);
  const [tasksState, setTasksState] = useState<Record<string, TaskState>>({});
  
  // Drag and drop events
  const onDragOver = (e: React.DragEvent) => { e.preventDefault(); };
  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleFilesSelected = (newFiles: File[]) => {
    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (idx: number) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  const clearAll = () => {
    setFiles([]);
    setTaskIds([]);
    setTasksState({});
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    // reset state
    setTasksState({});
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));

    try {
      const res = await axios.post(`${API_BASE}/extract`, formData);
      const ids = res.data.data.task_ids;
      setTaskIds(ids);
      const initialState: Record<string, TaskState> = {};
      ids.forEach((id: string) => {
        initialState[id] = { status: 'PROCESSING', progress: 0, message: '排队中...', result: null };
      });
      setTasksState(initialState);
    } catch (err) {
      console.error(err);
      alert('上传失败，请检查后端运行状态。');
    }
  };

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (taskIds.length > 0) {
      const checkTasks = async () => {
        let allDone = true;
        
        for (const id of taskIds) {
          // If already finished or failed, skip polling
          if (tasksState[id]?.status === 'COMPLETED' || tasksState[id]?.status === 'FAILED') {
            continue;
          }
          
          allDone = false; // still computing
          try {
            const res = await axios.get(`${API_BASE}/status/${id}`);
            const data = res.data;
            setTasksState(prev => ({
              ...prev,
              [id]: {
                status: data.status,
                progress: data.progress,
                message: data.message || '',
                result: data.result
              }
            }));
          } catch (err) {
            console.error("轮询失败", err);
          }
        }
        
        if (allDone) clearInterval(interval);
      };

      interval = setInterval(checkTasks, 2000);
      checkTasks(); // immediate check
    }

    return () => clearInterval(interval);
  }, [taskIds, tasksState]);

  const exportExcel = async () => {
    const resultsToExport = taskIds.map(id => tasksState[id]?.result).filter(r => r != null);
    if (resultsToExport.length === 0) {
      alert("没有可以导出的结果");
      return;
    }
    try {
      const res = await axios.post(`${API_BASE}/export`, resultsToExport, {
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
  };

  const isWorking = taskIds.some(id => tasksState[id]?.status === 'PROCESSING');
  const hasResults = taskIds.some(id => tasksState[id]?.status === 'COMPLETED');

  // Compute aggregate progress
  const totalProgress = taskIds.length > 0 
    ? taskIds.reduce((acc, id) => acc + (tasksState[id]?.progress || 0), 0) / taskIds.length 
    : 0;

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#1a1c29] to-black p-8 text-slate-200 font-sans">
      <header className="max-w-7xl mx-auto mb-12 text-center space-y-4">
        <div className="inline-flex items-center justify-center p-2 bg-slate-800/50 rounded-2xl border border-slate-700/50 mb-4 backdrop-blur-sm">
          <span className="flex h-3 w-3 relative mr-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
          </span>
          <span className="text-sm font-medium text-emerald-400">VLM Agent 已就绪</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">
          智能发票批量识别系统
        </h1>
        <p className="text-slate-400 max-w-2xl mx-auto font-light leading-relaxed">
          基于企业级多线程视觉大模型提取。支持批量PDF/图片文件，无感智能处理多页跨页合并逻辑。
        </p>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 左侧：多文件上传与预览区 */}
        <div className="glass-panel p-6 flex flex-col h-[75vh]">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-blue-300 flex items-center">
              <PlusCircle className="mr-2" />
              原始文件阵列
            </h2>
            <div className="space-x-3">
               {files.length > 0 && !isWorking && (
                  <button onClick={clearAll} className="px-3 py-1.5 text-sm bg-slate-800 text-slate-400 rounded hover:bg-slate-700 transition">清空</button>
               )}
               {files.length > 0 && taskIds.length === 0 && (
                 <button onClick={uploadFiles} className="px-4 py-2 bg-indigo-600/90 hover:bg-indigo-500 backdrop-blur text-sm rounded-lg shadow-xl shadow-indigo-500/30 transition-colors inline-flex items-center">
                   <CheckCircle className="w-4 h-4 mr-2" />
                   开始批量识别
                 </button>
               )}
            </div>
          </div>

          <div 
            onDragOver={onDragOver} 
            onDrop={onDrop}
            className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-700 rounded-xl bg-slate-800/30 hover:bg-slate-800/50 transition duration-300 relative overflow-y-auto w-full group"
          >
            {files.length === 0 ? (
               <label className="absolute inset-0 flex flex-col items-center justify-center cursor-pointer w-full h-full">
                  <div className="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mb-6 border border-blue-500/20 group-hover:scale-110 transition-transform">
                    <UploadCloud className="w-10 h-10 text-blue-400" />
                  </div>
                  <h3 className="text-xl font-medium text-slate-200 mb-2">拖拽多个发票文件至此</h3>
                  <p className="text-slate-500 text-sm">支持 PDF, PNG, JPG, JPEG, WEBP 格式 (多选)</p>
                  <input type="file" multiple className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => e.target.files && handleFilesSelected(Array.from(e.target.files))} />
               </label>
            ) : (
               <div className="w-full h-full overflow-y-auto p-4 custom-scrollbar">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                     {files.map((file, idx) => (
                        <div key={idx} className="relative group bg-slate-900 rounded-lg p-3 border border-slate-700 hover:border-slate-500">
                           <div className="text-sm truncate w-full text-slate-300 mb-1">{file.name}</div>
                           <div className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</div>
                           {taskIds.length === 0 && (
                              <button onClick={() => removeFile(idx)} className="absolute top-2 right-2 text-red-400 bg-red-900/50 rounded-full w-5 h-5 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">×</button>
                           )}
                        </div>
                     ))}
                     {taskIds.length === 0 && (
                        <label className="border-2 border-dashed border-slate-700 rounded-lg flex flex-col items-center justify-center text-slate-500 hover:text-blue-400 hover:border-blue-400 cursor-pointer min-h-[80px] transition-colors">
                           <PlusCircle className="w-6 h-6 mb-1" />
                           <span className="text-xs">添加更多</span>
                           <input type="file" multiple className="hidden" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => e.target.files && handleFilesSelected(Array.from(e.target.files))} />
                        </label>
                     )}
                  </div>
               </div>
            )}
          </div>
        </div>

        {/* 右侧：结果 */}
        <div className="glass-panel p-6 flex flex-col h-[75vh] relative">
           <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-emerald-300 flex items-center">
                <CheckCircle className="mr-2" />
                批量提取结果
              </h2>
              {hasResults && (
                <button onClick={exportExcel} className="flex items-center text-sm px-4 py-2 bg-emerald-600/20 text-emerald-300 border border-emerald-500/50 rounded-lg hover:bg-emerald-600/40 transition-colors">
                  <FileSpreadsheet className="w-4 h-4 mr-2" />
                  导出 汇总Excel
                </button>
              )}
           </div>

           {taskIds.length === 0 && (
             <div className="flex-1 flex items-center justify-center text-slate-500">
               等待任务触发...
             </div>
           )}

           {isWorking && (
             <div className="flex-1 flex flex-col items-center justify-center space-y-6">
               <Loader className="w-12 h-12 text-blue-400 animate-spin" />
               <div className="w-3/4 bg-slate-700 rounded-full h-2.5 overflow-hidden">
                 <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-2.5 rounded-full transition-all duration-500 ease-out" style={{ width: `${Math.max(totalProgress, 5)}%` }}></div>
               </div>
               <p className="text-blue-300 animate-pulse font-medium">批量处理中... (平均进度: {totalProgress.toFixed(0)}%)</p>
               <div className="w-full text-xs text-slate-500 px-10 max-h-32 overflow-y-auto">
                 {taskIds.map(id => (
                    <div key={id} className="flex justify-between mt-1">
                      <span className="truncate w-1/3">任务 {id.slice(0, 8)}</span>
                      <span className="w-1/3 text-center text-indigo-300">{tasksState[id]?.message}</span>
                      <span className="w-1/3 text-right">{tasksState[id]?.progress}%</span>
                    </div>
                 ))}
               </div>
             </div>
           )}

           {!isWorking && hasResults && (
             <div className="flex-1 overflow-y-auto space-y-8 custom-scrollbar pr-2">
               {taskIds.map((id, fileIndex) => {
                 const tState = tasksState[id];
                 if (tState?.status === 'FAILED') return (
                   <div key={id} className="bg-red-900/20 p-4 border border-red-800 rounded-lg text-red-400">
                     文件 {fileIndex + 1} 识别失败: {tState.message}
                   </div>
                 );
                 if (!tState?.result) return null;
                 const { file_name, invoices } = tState.result;

                 return (
                   <div key={id} className="bg-slate-800/40 rounded-xl p-4 border border-slate-700/50 relative overflow-hidden">
                     <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
                        <span className="text-blue-300 font-medium">来源文件: {file_name}</span>
                        <span className="text-xs text-slate-500">检测到 {invoices?.length || 0} 张发票</span>
                     </div>
                     
                     <div className="space-y-6">
                     {(invoices || []).map((invoice: any, idx: number) => (
                       <div key={idx} className="bg-slate-800/60 rounded-xl p-6 border border-slate-700/50 relative">
                         <div className="absolute top-0 right-0 bg-blue-600/20 text-blue-400 text-xs py-1 px-3 rounded-bl-lg font-bold border-b border-l border-blue-500/30">
                           子发票 #{idx + 1}
                         </div>
                         
                         <div className="grid grid-cols-2 gap-4 mt-2">
                           <Field label="发票号码" value={invoice.invoice_number} />
                           <Field label="发票日期" value={invoice.invoice_date} />
                           <Field label="总计金额" value={invoice.total_amount ? `${invoice.currency || ''} ${invoice.total_amount}` : null} />
                           <Field label="销方/商家" value={invoice.vendor_name} />
                           <Field label="购买方" value={invoice.purchaser_name} className="col-span-2" />
                         </div>

                         {invoice.items && invoice.items.length > 0 && (
                           <div className="mt-6">
                             <table className="w-full text-left text-xs bg-slate-900 rounded-lg overflow-hidden border border-slate-700/50">
                               <thead className="bg-slate-800 text-slate-400">
                                 <tr>
                                   <th className="px-3 py-2 rounded-tl-lg">描述</th>
                                   <th className="px-3 py-2">数量</th>
                                   <th className="px-3 py-2">单价</th>
                                   <th className="px-3 py-2 rounded-tr-lg">金额</th>
                                 </tr>
                               </thead>
                               <tbody className="divide-y divide-slate-700/50">
                                 {invoice.items.map((item: any, i: number) => (
                                   <tr key={i} className="hover:bg-slate-800/50 transition-colors">
                                     <td className="px-3 py-2">{item.description || '-'}</td>
                                     <td className="px-3 py-2">{item.quantity || '-'}</td>
                                     <td className="px-3 py-2">{item.unit_price || '-'}</td>
                                     <td className="px-3 py-2 font-medium text-emerald-400">{item.amount || '-'}</td>
                                   </tr>
                                 ))}
                               </tbody>
                             </table>
                           </div>
                         )}
                       </div>
                     ))}
                     </div>
                   </div>
                 );
               })}
             </div>
           )}
        </div>

      </main>
    </div>
  );
}

function Field({ label, value, className = '' }: { label: string, value: string | null | undefined, className?: string }) {
  return (
    <div className={`p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-blue-500/30 transition-colors ${className}`}>
      <div className="text-xs text-slate-400 font-medium mb-1">{label}</div>
      <div className="text-slate-100 font-semibold truncate">{value ? value : <span className="text-slate-600 italic">未提取/需人工录入</span>}</div>
    </div>
  );
}

export default App;
