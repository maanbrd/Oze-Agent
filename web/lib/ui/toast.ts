import { toast } from "sonner";

export const showSuccess = (title: string, body?: string) =>
  toast.success(title, { description: body, duration: 6000 });

export const showError = (
  title: string,
  body?: string,
  retry?: () => void,
) =>
  toast.error(title, {
    description: body,
    duration: 8000,
    action: retry ? { label: "Spróbuj ponownie", onClick: retry } : undefined,
  });

export const showAction = (
  title: string,
  body: string,
  undo: () => void,
) =>
  toast(title, {
    description: body,
    duration: 6000,
    action: { label: "Cofnij", onClick: undo },
  });

export function showPromise<T>(
  promise: Promise<T>,
  msgs: { loading: string; success: string; error: string },
) {
  return toast.promise(promise, msgs);
}
