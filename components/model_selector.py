import streamlit as st

from config.settings import PROVIDER_DEFAULTS, SUPPORTED_PROVIDERS, Settings


def _mask_api_key(api_key: str) -> str:
    if not api_key:
        return "(empty)"
    if len(api_key) <= 8:
        return "*" * len(api_key)
    return f"{api_key[:4]}{'*' * (len(api_key) - 8)}{api_key[-4:]}"


def render_model_selector(settings: Settings) -> dict[str, str]:
    with st.container(border=True):
        st.subheader("模型与接口配置")
        st.caption("这里可以直接选择模型服务、填写 Base URL 和 API Key。保存后当前进程会立即使用新配置。")

        provider_options = SUPPORTED_PROVIDERS
        current_provider = settings.provider if settings.provider in provider_options else "openai_compatible"
        provider_index = provider_options.index(current_provider)
        provider = st.selectbox(
            "模型服务商",
            provider_options,
            index=provider_index,
            format_func=lambda item: PROVIDER_DEFAULTS[item]["label"],
            key="settings_provider_select",
        )

        provider_defaults = PROVIDER_DEFAULTS[provider]
        preset_models = provider_defaults["models"]
        use_custom_base_url = st.toggle(
            "自定义 Base URL",
            value=bool(settings.base_url and settings.base_url != provider_defaults["base_url"]),
            key="settings_custom_base_url_toggle",
        )

        base_url_default = settings.base_url if use_custom_base_url else provider_defaults["base_url"]
        base_url = st.text_input(
            "Base URL",
            value=base_url_default,
            key="settings_base_url_input",
            placeholder="例如：https://api.openai.com/v1",
        )

        if preset_models:
            model_mode_options = ["从推荐模型中选择", "手动填写模型名称"]
            model_mode = st.radio(
                "模型选择方式",
                model_mode_options,
                horizontal=True,
                key="settings_model_mode",
                index=0 if settings.model in preset_models else 1,
            )
            if model_mode == "从推荐模型中选择":
                model_index = preset_models.index(settings.model) if settings.model in preset_models else 0
                model = st.selectbox(
                    "推荐模型",
                    preset_models,
                    index=model_index,
                    key="settings_model_select",
                )
            else:
                model = st.text_input(
                    "模型名称",
                    value=settings.model,
                    key="settings_model_input",
                    placeholder="例如：deepseek-ai/DeepSeek-V3",
                )
        else:
            model = st.text_input(
                "模型名称",
                value=settings.model,
                key="settings_model_input",
                placeholder="例如：gpt-4o-mini / your-compatible-model",
            )

        api_key = st.text_input(
            "API Key",
            value=settings.api_key,
            type="password",
            key="settings_api_key_input",
            placeholder="请输入模型平台 API Key",
        )

        st.caption(f"当前已载入的 API Key：{_mask_api_key(settings.api_key)}")

        st.markdown("**目录配置**")
        uploads_dir = st.text_input("上传目录", value=settings.uploads_dir, key="settings_uploads_dir_input")
        outputs_dir = st.text_input("导出目录", value=settings.outputs_dir, key="settings_outputs_dir_input")
        cache_dir = st.text_input("缓存目录", value=settings.cache_dir, key="settings_cache_dir_input")

    return {
        "provider": provider,
        "base_url": base_url.strip(),
        "api_key": api_key.strip(),
        "model": model.strip(),
        "uploads_dir": uploads_dir.strip(),
        "outputs_dir": outputs_dir.strip(),
        "cache_dir": cache_dir.strip(),
    }
