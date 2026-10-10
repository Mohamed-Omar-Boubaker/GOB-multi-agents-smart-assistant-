import React, { useEffect, useRef, useState } from 'react';
import { apiService } from '../../services/api';
import './ContactManagerPanel.css';

type ContactAliasMap = Record<string, string>;

type ContactMap = Record<string, {
  name: string;
  email: string;
  phone?: string;
  tags?: string[];
}>;

interface ContactItem {
  name: string;
  email: string;
  phone: string;
  tags: string[];
}

const toContactList = (contacts: ContactMap): ContactItem[] => {
  return Object.entries(contacts).map(([, contact]) => ({
    name: contact.name,
    email: contact.email,
    phone: contact.phone || '',
    tags: contact.tags || []
  }));
};

const ContactManagerPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contacts, setContacts] = useState<ContactItem[]>([]);
  const [aliases, setAliases] = useState<ContactAliasMap>({});

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [tags, setTags] = useState('');

  const [aliasName, setAliasName] = useState('');
  const [aliasContactName, setAliasContactName] = useState('');

  const [fabPosition, setFabPosition] = useState({ x: 0, y: 0 });
  const dragStateRef = useRef({
    dragging: false,
    moved: false,
    startX: 0,
    startY: 0,
    offsetX: 0,
    offsetY: 0
  });

  const fetchContacts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getContactsConfig();
      setContacts(toContactList(data.contacts || {}));
      setAliases(data.aliases || {});
    } catch (err: any) {
      console.error('Failed to fetch contacts', err);
      setError('Failed to load contacts');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchContacts();
    }
  }, [isOpen]);

  useEffect(() => {
    const setDefaultPosition = () => {
      const margin = 16;
      const size = 50;
      const gap = 12;
      const x = margin;
      const baseY = window.innerHeight - size - 120;
      const y = Math.max(margin, baseY - (size + gap));
      setFabPosition({ x, y });
    };

    setDefaultPosition();
    window.addEventListener('resize', setDefaultPosition);

    return () => {
      window.removeEventListener('resize', setDefaultPosition);
    };
  }, []);

  const handleFabPointerDown = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.setPointerCapture(event.pointerId);

    dragStateRef.current.dragging = true;
    dragStateRef.current.moved = false;
    dragStateRef.current.startX = event.clientX;
    dragStateRef.current.startY = event.clientY;
    dragStateRef.current.offsetX = event.clientX - fabPosition.x;
    dragStateRef.current.offsetY = event.clientY - fabPosition.y;
  };

  const handleFabPointerMove = (event: React.PointerEvent<HTMLButtonElement>) => {
    if (!dragStateRef.current.dragging) return;

    const deltaX = Math.abs(event.clientX - dragStateRef.current.startX);
    const deltaY = Math.abs(event.clientY - dragStateRef.current.startY);
    if (deltaX > 4 || deltaY > 4) {
      dragStateRef.current.moved = true;
    }

    const size = 50;
    const margin = 8;
    const maxX = window.innerWidth - size - margin;
    const maxY = window.innerHeight - size - margin;
    const nextX = Math.min(Math.max(margin, event.clientX - dragStateRef.current.offsetX), maxX);
    const nextY = Math.min(Math.max(margin, event.clientY - dragStateRef.current.offsetY), maxY);

    setFabPosition({ x: nextX, y: nextY });
  };

  const handleFabPointerUp = (event: React.PointerEvent<HTMLButtonElement>) => {
    const button = event.currentTarget;
    button.releasePointerCapture(event.pointerId);

    const wasMoved = dragStateRef.current.moved;
    dragStateRef.current.dragging = false;

    if (!wasMoved) {
      setIsOpen(true);
    }
  };

  const resetForm = () => {
    setName('');
    setEmail('');
    setPhone('');
    setTags('');
  };

  const submitContact = async () => {
    if (!name || !email) {
      setError('Name and email are required');
      return;
    }

    const tagList = tags
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    setError(null);
    try {
      await apiService.addContact({
        name,
        email,
        phone,
        tags: tagList
      });
      resetForm();
      fetchContacts();
    } catch (err: any) {
      console.error('Failed to save contact', err);
      setError('Failed to save contact');
    }
  };

  const updateContact = async () => {
    if (!name) {
      setError('Name is required');
      return;
    }

    const tagList = tags
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    setError(null);
    try {
      await apiService.updateContact(name, {
        name: name || undefined,
        email: email || undefined,
        phone: phone || undefined,
        tags: tags ? tagList : undefined
      });
      resetForm();
      fetchContacts();
    } catch (err: any) {
      console.error('Failed to update contact', err);
      setError('Failed to update contact');
    }
  };

  const deleteContact = async (item: ContactItem) => {
    setError(null);
    try {
      await apiService.deleteContact(item.name);
      fetchContacts();
    } catch (err: any) {
      console.error('Failed to delete contact', err);
      setError('Failed to delete contact');
    }
  };

  const startEdit = (item: ContactItem) => {
    setName(item.name);
    setEmail(item.email);
    setPhone(item.phone || '');
    setTags((item.tags || []).join(', '));
  };

  const addAlias = async () => {
    if (!aliasName || !aliasContactName) {
      setError('Alias and contact name are required');
      return;
    }

    setError(null);
    try {
      await apiService.addContactAlias({ alias: aliasName, contact_name: aliasContactName });
      setAliasName('');
      setAliasContactName('');
      fetchContacts();
    } catch (err: any) {
      console.error('Failed to add alias', err);
      setError('Failed to add alias');
    }
  };

  const deleteAlias = async (alias: string) => {
    setError(null);
    try {
      await apiService.deleteContactAlias(alias);
      fetchContacts();
    } catch (err: any) {
      console.error('Failed to delete alias', err);
      setError('Failed to delete alias');
    }
  };

  return (
    <>
      <button
        className="contact-manager-trigger"
        style={{ left: `${fabPosition.x}px`, top: `${fabPosition.y}px` }}
        onPointerDown={handleFabPointerDown}
        onPointerMove={handleFabPointerMove}
        onPointerUp={handleFabPointerUp}
        onPointerCancel={handleFabPointerUp}
        title="Contact Manager"
      >
        👤
      </button>

      {isOpen && (
        <div className="contact-manager-overlay" onClick={() => setIsOpen(false)}>
          <div className="contact-manager-panel" onClick={(e) => e.stopPropagation()}>
            <div className="contact-manager-header">
              <div className="contact-manager-title">Contact Manager</div>
              <button className="contact-manager-close" onClick={() => setIsOpen(false)}>
                X
              </button>
            </div>

            <div className="contact-manager-content">
              {error && <div className="contact-manager-error">{error}</div>}

              <section className="contact-manager-section">
                <h3>Contacts</h3>
                {loading ? (
                  <div className="contact-manager-loading">Loading...</div>
                ) : (
                  <div className="contact-manager-list">
                    {contacts.map((item) => (
                      <div key={item.name} className="contact-manager-row">
                        <div className="contact-manager-row-main">
                          <div className="contact-manager-row-title">{item.name}</div>
                          <div className="contact-manager-row-sub">
                            {item.email}
                          </div>
                        </div>
                        <div className="contact-manager-row-actions">
                          <button onClick={() => startEdit(item)}>Edit</button>
                          <button onClick={() => deleteContact(item)}>Delete</button>
                        </div>
                      </div>
                    ))}
                    {contacts.length === 0 && <div className="contact-manager-empty">No contacts yet</div>}
                  </div>
                )}
              </section>

              <section className="contact-manager-section">
                <h3>Add Contact</h3>
                <div className="contact-manager-form">
                  <input
                    type="text"
                    placeholder="Name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Phone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Tags (comma separated)"
                    value={tags}
                    onChange={(e) => setTags(e.target.value)}
                  />
                  <div className="contact-manager-form-actions">
                    <button onClick={submitContact}>Add</button>
                    <button onClick={updateContact} className="secondary">Update</button>
                    <button onClick={resetForm} className="secondary">Clear</button>
                  </div>
                </div>
              </section>

              <section className="contact-manager-section">
                <h3>Aliases</h3>
                <div className="contact-manager-list">
                  {Object.entries(aliases).map(([alias, target]) => (
                    <div key={alias} className="contact-manager-row">
                      <div className="contact-manager-row-main">
                        <div className="contact-manager-row-title">{alias}</div>
                        <div className="contact-manager-row-sub">{target}</div>
                      </div>
                      <div className="contact-manager-row-actions">
                        <button onClick={() => deleteAlias(alias)}>Delete</button>
                      </div>
                    </div>
                  ))}
                  {Object.keys(aliases).length === 0 && (
                    <div className="contact-manager-empty">No aliases yet</div>
                  )}
                </div>
                <div className="contact-manager-form">
                  <input
                    type="text"
                    placeholder="Alias"
                    value={aliasName}
                    onChange={(e) => setAliasName(e.target.value)}
                  />
                  <input
                    type="text"
                    placeholder="Contact name target"
                    value={aliasContactName}
                    onChange={(e) => setAliasContactName(e.target.value)}
                  />
                  <div className="contact-manager-form-actions">
                    <button onClick={addAlias}>Add Alias</button>
                  </div>
                </div>
              </section>
            </div>

            <div className="contact-manager-footer">
              <button onClick={fetchContacts} className="secondary">Refresh</button>
              <button onClick={() => setIsOpen(false)}>Done</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ContactManagerPanel;
