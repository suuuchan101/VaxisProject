using System;
using System.Text;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace VAXIS.Core
{
    /// <summary>
    /// Unity から ComfyUI API へプロンプトを送信する通信ブリッジクラス。
    /// 最小構成として /prompt エンドポイントへの POST 通信を実装。
    /// </summary>
    public static class VAXISComfyBridge
    {
        public class Response
        {
            public string prompt_id;
            public int number;
            // 必要に応じてエラー情報などを拡張
        }

        /// <summary>
        /// ComfyUI へプロンプトを送信します（非同期コルーチン）。
        /// </summary>
        /// <param name="baseUrl">接続先 URL</param>
        /// <param name="promptJson">ワークフローを表す JSON 文字列</param>
        /// <param name="onSuccess">成功時のコールバック</param>
        /// <param name="onError">失敗時のコールバック</param>
        public static IEnumerator PostPrompt(string baseUrl, string promptJson, Action<Response> onSuccess, Action<string> onError)
        {
            // エンドポイント URL の構築
            string url = baseUrl.TrimEnd('/') + "/prompt";
            
            // リクエストボディの作成
            string jsonPayload = $"{{\"prompt\": {promptJson}}}";
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonPayload);

            using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
            {
                request.uploadHandler = new UploadHandlerRaw(bodyRaw);
                request.downloadHandler = new DownloadHandlerBuffer();
                request.SetRequestHeader("Content-Type", "application/json");

                // 通信の開始
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    // 成功時
                    string resJson = request.downloadHandler.text;
                    Response res = JsonUtility.FromJson<Response>(resJson);
                    onSuccess?.Invoke(res);
                }
                else
                {
                    // 失敗時
                    string errorMsg = $"[VAXIS Bridge] Error: {request.error}\nResponse: {request.downloadHandler.text}";
                    Debug.LogError(errorMsg);
                    onError?.Invoke(errorMsg);
                }
            }
        }
    }
}

// 著作者: VAXIS Development Team
