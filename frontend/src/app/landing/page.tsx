import { redirect } from "next/navigation";

/** Legacy preview route — premium landing is now the homepage. */
export default function LandingRedirect() {
  redirect("/");
}
