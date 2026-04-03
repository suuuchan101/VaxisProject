using UnityEngine;

namespace VAXIS.Core
{
    /// <summary>
    /// VAXIS Core の設定を保持する ScriptableObject。
    /// ComfyUI の接続先 URL などをエディタ上で永続化します。
    /// </summary>
    [CreateAssetMenu(fileName = "VAXISSettings", menuName = "VAXIS/Core/Settings")]
    public class VAXISSettings : ScriptableObject
    {
        [Header("ComfyUI Connectivity")]
        [Tooltip("ComfyUI API のベース URL (例: http://127.0.0.1:8188)")]
        public string comfyUrl = "http://127.0.0.1:8188";

        // 今後、APIキーやデフォルトの生成設定などをここに追加可能です。
    }
}

// 著作者: VAXIS Development Team
