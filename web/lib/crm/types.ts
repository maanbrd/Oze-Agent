export type FunnelStatus =
  | "Nowy lead"
  | "Spotkanie umówione"
  | "Spotkanie odbyte"
  | "Oferta wysłana"
  | "Podpisane"
  | "Zamontowana"
  | "Rezygnacja z umowy"
  | "Nieaktywny"
  | "Odrzucone";

export type CrmClient = {
  id: string;
  fullName: string;
  city: string;
  phone: string | null;
  email: string | null;
  address: string | null;
  product: string | null;
  status: FunnelStatus;
  notes: string | null;
  lastContactAt: string | null;
  nextAction: string | null;
  nextActionAt: string | null;
  sheetsUrl: string | null;
  calendarUrl: string | null;
  driveUrl: string | null;
};

export type CrmEventType =
  | "in_person"
  | "phone_call"
  | "offer_email"
  | "doc_followup";

export type CrmEvent = {
  id: string;
  clientId: string | null;
  title: string;
  clientName: string;
  city: string | null;
  startsAt: string;
  endsAt: string;
  type: CrmEventType;
  location: string | null;
  calendarUrl: string | null;
};

export type CrmDashboardData = {
  fetchedAt: string;
  clients: CrmClient[];
  events: CrmEvent[];
};
