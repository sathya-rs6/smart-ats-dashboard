import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  X, 
  Upload, 
  File, 
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';

export const UploadModal = ({ isOpen, onClose, onUploadComplete }) => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles) => {
    setFiles(prev => [...prev, ...acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending'
    }))]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
  });

  const removeFile = (id) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const handleUpload = async () => {
    setUploading(true);
    setProgress(0);
    
    try {
      await api.bulkUploadResumes(files, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProgress(percentCompleted);
      });
      
      onUploadComplete(files);
      onClose();
      setFiles([]);
    } catch (error) {
      console.error("Upload failed:", error);
      // Ideally show an error toast here
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm" onClick={onClose} />
      
      <div className="relative glass-card w-full max-w-xl shadow-2xl animate-scale-in">
        <div className="p-6 border-b border-slate-200 flex justify-between items-center">
          <h3 className="text-xl font-bold font-['Outfit']">Bulk Resume Upload</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-xl transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-8">
          <div 
            {...getRootProps()} 
            className={`
              border-2 border-dashed rounded-3xl p-10 flex flex-col items-center justify-center transition-all cursor-pointer
              ${isDragActive ? 'border-slate-900 bg-slate-50' : 'border-slate-200 hover:border-slate-400 hover:bg-white/[0.02]'}
            `}
          >
            <input {...getInputProps()} />
            <div className="mb-4 p-4 bg-slate-100 rounded-2xl text-slate-900">
              <Upload size={32} />
            </div>
            <p className="text-lg font-semibold mb-1">
              {isDragActive ? 'Drop files here' : 'Click or drag files to upload'}
            </p>
            <p className="text-sm text-slate-500 text-center">
              Support PDF and DOCX files. <br /> Max 10MB per file.
            </p>
          </div>

          {files.length > 0 && (
            <div className="mt-8 space-y-3 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
              {files.map((f) => (
                <div key={f.id} className="flex items-center justify-between p-3 bg-white/5 rounded-2xl border border-slate-200">
                  <div className="flex items-center gap-3">
                    <File size={20} className="text-slate-500" />
                    <div>
                      <p className="text-sm font-medium truncate max-w-[200px]">{f.file.name}</p>
                      <p className="text-[10px] text-slate-500">{(f.file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button onClick={() => removeFile(f.id)} className="p-1 hover:bg-white/5 rounded-lg text-slate-500 hover:text-red-400">
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 border-t border-slate-200 flex gap-3">
          <button 
            onClick={onClose}
            className="flex-1 py-3 border border-slate-200 rounded-2xl font-semibold hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button 
            disabled={files.length === 0 || uploading}
            onClick={handleUpload}
            className="flex-1 py-3 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed rounded-2xl font-bold transition-all shadow-lg shadow-sm flex items-center justify-center gap-2"
          >
            {uploading ? (
              <>
                <Loader2 size={20} className="animate-spin" />
                <span>Uploading {progress}%</span>
              </>
            ) : (
              <span>Start Analysis</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
