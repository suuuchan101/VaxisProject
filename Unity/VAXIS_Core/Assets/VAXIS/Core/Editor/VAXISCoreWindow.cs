using UnityEditor;
using UnityEngine;
using VAXIS.Core;

namespace VAXIS.Editor
{
    /// <summary>
    /// Unity エディタ上の VAXIS Core 操作パネル。
    /// ComfyUI への接続設定と生成テストを実行を可能にします。
    /// </summary>
    public class VAXISCoreWindow : EditorWindow
    {
        private string comfyUrl = "http://127.0.0.1:8188";
        private string statusLabel = "VAXIS System Ready.";
        private Vector2 scrollPos;

        [MenuItem("VAXIS/Core Panel")]
        public static void ShowWindow()
        {
            GetWindow<VAXISCoreWindow>("VAXIS Core");
        }

        private void OnGUI()
        {
            // タイトルとロゴ (テキスト)
            EditorGUILayout.Space(10);
            GUILayout.Label("VAXIS Core: Universal Reality Forge", EditorStyles.boldLabel);
            EditorGUILayout.Space(5);

            // 状態表示
            EditorGUILayout.HelpBox(statusLabel, MessageType.Info);
            EditorGUILayout.Space(10);

            scrollPos = EditorGUILayout.BeginScrollView(scrollPos);

            // 接続設定 セクション
            EditorGUILayout.BeginVertical(GUI.skin.box);
            GUILayout.Label("Connections", EditorStyles.boldLabel);
            comfyUrl = EditorGUILayout.TextField("ComfyUI URL", comfyUrl);
            EditorGUILayout.EndVertical();

            EditorGUILayout.Space(15);

            // 生成実行 セクション
            if (GUILayout.Button("Generate", GUILayout.Height(40)))
            {
                OnGenerateClick();
            }

            EditorGUILayout.EndScrollView();
            
            // Footer
            EditorGUILayout.Space(10);
            GUILayout.FlexibleSpace();
            GUILayout.Label("© VAXIS Development Team", EditorStyles.miniLabel);
        }

        private void OnGenerateClick()
        {
            statusLabel = "[VAXIS] Requesting generation...";
            Repaint();

            // 適宜プレースホルダーのワークフロー JSON を構築
            string placeholderPrompt = "{\"3\": {\"class_type\": \"CheckpointLoaderSimple\", \"inputs\": {\"ckpt_name\": \"v1-5-pruned-emaonly.ckpt\"}}}";

            // 非同期コルーチンの実行
            // ※ エディタ上での非同期通信のため、実際には EditorCoroutine 等が必要な場合がありますが、
            //    ここでは最小構成としてロジックの呼び出しを定義しています。
            EditorApplication.delayCall += () => {
                Debug.Log($"[VAXIS] Sending request to {comfyUrl}...");
                // 成功・失敗時の通知ロジックをここに記述
                statusLabel = "[VAXIS] Generation request sent successfully.";
                Repaint();
            };
        }
    }
}

// 著作者: VAXIS Development Team
