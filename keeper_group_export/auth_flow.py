"""Keeper LoginUi implementation and connected-session transition."""

from tkinter import messagebox, simpledialog

from .common import APP_TITLE, C_DANGER, C_MUTED, C_SUCCESS


class AuthFlowMixin:
    def _make_keeper_login_ui(self):
        """Create Keeper's LoginUi contract using native Tk dialogs.

        Keeper remains the authority for authentication, cryptography and token
        validation. This adapter supplies only operator interaction for each
        state requested by Keeper's LoginV3 flow.
        """
        app = self
        steps = self.k_login_steps

        class TkLoginUi(steps.LoginUi):
            def on_device_approval(self, step):
                choices = [
                    "Email approval link",
                    "Keeper Push to an approved device",
                    "Enter a verification code",
                    "I already approved it — check again",
                    "Cancel sign-in",
                ]

                choice = app._choose_from_list(
                    "Keeper Device Approval",
                    "Keeper needs to approve this computer for this account.",
                    choices,
                )

                if choice is None or choice == 4:
                    step.cancel()
                    return

                if choice == 0:
                    try:
                        step.send_push(steps.DeviceApprovalChannel.Email)
                    except Exception as exc:
                        messagebox.showerror(
                            "Keeper Device Approval",
                            f"Keeper could not send the approval email.\n\n{exc}",
                            parent=app,
                        )
                        return

                    messagebox.showinfo(
                        "Keeper Device Approval",
                        "Keeper sent an approval message.\n\n"
                        "Open it and approve this device, then click OK here.",
                        parent=app,
                    )
                    step.resume()
                    return

                if choice == 1:
                    try:
                        step.send_push(steps.DeviceApprovalChannel.KeeperPush)
                    except Exception as exc:
                        messagebox.showerror(
                            "Keeper Device Approval",
                            f"Keeper could not send the push notification.\n\n{exc}",
                            parent=app,
                        )
                        return

                    messagebox.showinfo(
                        "Keeper Device Approval",
                        "Approve the sign-in on an existing Keeper device, then "
                        "click OK here.",
                        parent=app,
                    )
                    step.resume()
                    return

                if choice == 2:
                    code = simpledialog.askstring(
                        "Keeper Device Approval",
                        "Enter the Keeper device verification code:",
                        parent=app,
                    )
                    if not code:
                        return

                    last_error = None
                    for channel in (
                        steps.DeviceApprovalChannel.Email,
                        steps.DeviceApprovalChannel.TwoFactor,
                    ):
                        try:
                            step.send_code(channel, code.strip())
                            return
                        except Exception as exc:
                            last_error = exc

                    messagebox.showerror(
                        "Keeper Device Approval",
                        "Keeper did not accept that verification code."
                        + (f"\n\n{last_error}" if last_error else ""),
                        parent=app,
                    )
                    return

                step.resume()

            def on_two_factor(self, step):
                channels = list(step.get_channels() or ())
                if not channels:
                    step.cancel()
                    return

                def describe(channel):
                    labels = {
                        steps.TwoFactorChannel.Authenticator: "Authenticator app",
                        steps.TwoFactorChannel.TextMessage: "SMS",
                        steps.TwoFactorChannel.DuoSecurity: "Duo Security",
                        steps.TwoFactorChannel.RSASecurID: "RSA SecurID",
                        steps.TwoFactorChannel.KeeperDNA: "Keeper DNA",
                        steps.TwoFactorChannel.SecurityKey: "Security key / WebAuthn",
                        steps.TwoFactorChannel.Backup: "Backup code",
                    }
                    label = labels.get(channel.channel_type, "Other factor")
                    details = " ".join(
                        str(value).strip()
                        for value in (channel.channel_name, channel.phone)
                        if value
                    )
                    return f"{label}{(' — ' + details) if details else ''}"

                # Keeper Commander's WebAuthn path requires browser/security-key
                # handling this Tk utility does not currently implement.
                usable = [
                    channel
                    for channel in channels
                    if channel.channel_type != steps.TwoFactorChannel.SecurityKey
                ]

                if not usable:
                    messagebox.showerror(
                        "Keeper Two-Factor Authentication",
                        "This account currently offers only a WebAuthn/security-key "
                        "factor, which this utility does not yet support.",
                        parent=app,
                    )
                    step.cancel()
                    return

                if len(usable) == 1:
                    channel = usable[0]
                else:
                    index = app._choose_from_list(
                        "Keeper Two-Factor Authentication",
                        "Choose the Keeper verification method:",
                        [describe(channel) for channel in usable],
                    )
                    if index is None:
                        step.cancel()
                        return
                    channel = usable[index]

                if channel.channel_type == steps.TwoFactorChannel.TextMessage:
                    try:
                        step.send_push(
                            channel.channel_uid,
                            steps.TwoFactorPushAction.TextMessage,
                        )
                    except Exception as exc:
                        messagebox.showerror(
                            "Keeper Two-Factor Authentication",
                            f"Keeper could not send the SMS code.\n\n{exc}",
                            parent=app,
                        )
                        return

                while True:
                    code = simpledialog.askstring(
                        "Keeper Two-Factor Authentication",
                        f"{describe(channel)}\n\nEnter the Keeper verification code:",
                        parent=app,
                    )
                    if code is None:
                        step.cancel()
                        return
                    if not code.strip():
                        continue

                    # Do not silently extend the user's remembered-2FA duration.
                    step.duration = steps.TwoFactorDuration.EveryLogin

                    try:
                        step.send_code(channel.channel_uid, code.strip())
                        return
                    except Exception as exc:
                        retry = messagebox.askretrycancel(
                            "Keeper Two-Factor Authentication",
                            f"Keeper did not accept that code.\n\n{exc}",
                            parent=app,
                        )
                        if not retry:
                            step.cancel()
                            return

            def on_password(self, step):
                first = app._login_password
                app._login_password = ""

                while True:
                    if first is not None:
                        password = first
                        first = None
                    else:
                        password = simpledialog.askstring(
                            "Keeper Master Password",
                            f"Enter the master password for {step.username}:",
                            show="•",
                            parent=app,
                        )

                    if not password:
                        step.cancel()
                        return

                    try:
                        step.verify_password(password)
                        return
                    except Exception as exc:
                        retry = messagebox.askretrycancel(
                            "Keeper Sign In",
                            f"Keeper did not accept the password.\n\n{exc}",
                            parent=app,
                        )
                        if not retry:
                            step.cancel()
                            return

            def on_sso_redirect(self, step):
                # The utility explicitly asks for a master password, so use
                # Keeper's supported alternate master-password path to SSO.
                step.login_with_password()

            def on_sso_data_key(self, step):
                try:
                    step.request_data_key(steps.DataKeyShareChannel.KeeperPush)
                    messagebox.showinfo(
                        "Keeper Approval",
                        "Approve the Keeper request on an existing device, then "
                        "click OK here.",
                        parent=app,
                    )
                    step.resume()
                except Exception:
                    try:
                        step.request_data_key(steps.DataKeyShareChannel.AdminApproval)
                        messagebox.showinfo(
                            "Keeper Approval",
                            "Administrator approval is required. Complete it, then "
                            "click OK here.",
                            parent=app,
                        )
                        step.resume()
                    except Exception as exc:
                        messagebox.showerror(
                            "Keeper Approval",
                            f"Keeper could not request the required approval.\n\n{exc}",
                            parent=app,
                        )
                        step.cancel()

        return TkLoginUi()

    def connect_keeper(self, user):
        """Authenticate, synchronise the vault and publish connected state."""
        self.conn_status.config(text="Authenticating with Keeper…", fg=C_MUTED)
        self._set_status("Authenticating with Keeper…", tone="info")
        self.update()

        try:
            params = self._new_keeper_params()
            params.user = user

            self.k_api.login(params, login_ui=self._make_keeper_login_ui())

            if not params.session_token:
                raise RuntimeError(
                    "Keeper authentication was cancelled or approval was not completed. "
                    "Try Connect again and complete the device-approval or 2FA prompt."
                )

            self.conn_status.config(text="Reading vault folders…")
            self._set_status("Reading vault folders…", tone="info")
            self.update()

            self.k_api.sync_down(params)

            self.params = params
            self._write_last_user(params.user or user)
            self.last_user = params.user or user
            self._load_folder_list()

            self.account_badge.config(
                text=params.user or user,
                bg="#243027",
                fg=C_SUCCESS,
            )
            self.conn_status.config(
                text=f"Connected • {len(self.folder_by_label)} folders available",
                fg=C_SUCCESS,
            )
            self.reload_btn.config(state="normal")
            self.refresh_btn.config(state="normal")
            self._set_status("Connected to Keeper", tone="success")

            if self.login_overlay is not None:
                self.login_overlay.destroy()
                self.login_overlay = None

        except KeyboardInterrupt:
            self._login_password = ""
            self.login_button.config(state="normal", text="Connect")
            self.login_error.config(text="Keeper sign-in was cancelled.")
            self._set_status("Keeper sign-in cancelled", tone="warning")
        except Exception as exc:
            self._login_password = ""
            if self.login_overlay is not None:
                self.login_button.config(state="normal", text="Connect")
                self.login_error.config(text=str(exc))
                self._set_status("Keeper sign-in failed", tone="danger")
            else:
                self.conn_status.config(text="Keeper connection failed", fg=C_DANGER)
                self._set_status("Keeper connection failed", tone="danger")
                messagebox.showerror(
                    APP_TITLE,
                    "Could not connect to Keeper.\n\n" + str(exc),
                    parent=self,
                )
